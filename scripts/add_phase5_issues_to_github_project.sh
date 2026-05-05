#!/usr/bin/env bash
# Add Phase 5 GitHub Issues to the org Project and set Phase = "Phase 5".
# Requires: gh CLI with read:project + project scopes (see `gh auth status`).
#   gh auth refresh -s read:project -s project -h github.com
#
# If the Project 「Phase」 field has no option named "Phase 5", this script
# appends it via GitHub GraphQL (updateProjectV2Field), preserving existing
# option colours.
set -euo pipefail

ORG="${ORG:-zyx-corporation}"
REPO="${REPO:-openayane-rde}"
PROJECT_TITLE="${PROJECT_TITLE:-OpenAyane RDE Implementation}"
PHASE_OPTION="${PHASE_OPTION:-Phase 5}"
ISSUES=(44 45 46 47 48 49 50 53 54)

# Populated by ensure_github_phase_option (bash 3.2-friendly).
_gh_phase_field_id=""
_gh_phase_select_option_id=""

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

check_gh_scope() {
  if ! gh project list --owner "$ORG" --limit 1 --format json >/dev/null 2>&1; then
    die "$(printf '%s\n%s\n' \
      'gh に project/read:project スコープがありません。次を実行してから再度このスクリプトを実行してください:' \
      '  gh auth refresh -s read:project -s project -h github.com')"
  fi
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

find_project_item_id() {
  local proj_num="$1" issue_url="$2"
  gh project item-list "$proj_num" --owner "$ORG" --format json -L 500 \
    | jq -r --arg u "$issue_url" \
      '.items[]?
        | select(.content.type == "Issue" and .content.url == $u)
        | .id' \
    | head -1
}

ensure_github_phase_option() {
  local project_node_id="$1"
  local want_name="$2"
  _gh_phase_field_id=""
  _gh_phase_select_option_id=""

  local query
  read -r -d '' query <<'GQ' || true
query ($id: ID!) {
  node(id: $id) {
    ... on ProjectV2 {
      field(name: "Phase") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
            color
            description
          }
        }
      }
    }
  }
}
GQ

  local resp
  resp="$(jq -n --arg q "$query" --arg id "$project_node_id" '{"query": $q, "variables": {"id": $id}}' | gh api graphql --input -)"

  _gh_phase_field_id="$(echo "$resp" | jq -r '.data.node.field.id // empty')"
  if [[ -z "$_gh_phase_field_id" ]]; then
    echo "$resp" | jq . >&2
    die "$(printf '%s\n' 'Phase フィールドを取得できません。Project と GraphQL 応答を確認してください。')"
  fi

  _gh_phase_select_option_id="$(echo "$resp" \
    | jq -r --arg w "$want_name" '.data.node.field.options[]? | select(.name == $w) | .id' \
    | head -1)"

  if [[ -n "${_gh_phase_select_option_id}" ]]; then
    return 0
  fi

  local mutation
  read -r -d '' mutation <<'GQ' || true
mutation ($input: UpdateProjectV2FieldInput!) {
  updateProjectV2Field(input: $input) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        options {
          id
          name
        }
      }
    }
  }
}
GQ

  local mut_body upd
  mut_body="$(echo "$resp" | jq \
    --arg mq "$mutation" \
    --arg fid "$_gh_phase_field_id" \
    --arg want "$want_name" '
    {
      "query": $mq,
      "variables": {
        "input": {
          "fieldId": $fid,
          "singleSelectOptions": (
            [.data.node.field.options[] |
              {
                id: .id,
                name: .name,
                color: .color,
                description: (.description // "")
              }
            ] + [{
              "name": $want,
              "color": (.data.node.field.options[-1].color // "GRAY"),
              "description": ""
            }]
          )
        }
      }
    }
  ')"

  upd="$(printf '%s' "$mut_body" | gh api graphql --input -)"
  if echo "$upd" | jq -e '.errors != null and (.errors | length > 0)' >/dev/null 2>&1; then
    echo "$upd" | jq . >&2
    die "$(printf '%s\n' \
      "Phase に「${want_name}」を追加できませんでした。Project で Phase 単一選択に「${want_name}」を追加してから再実行してください。")"
  fi

  _gh_phase_select_option_id="$(echo "$upd" \
    | jq -r --arg w "$want_name" '.data.updateProjectV2Field.projectV2Field.options[] | select(.name == $w) | .id' \
    | head -1)"

  if [[ -z "${_gh_phase_select_option_id}" ]]; then
    echo "$upd" | jq . >&2
    die "$(printf '%s\n' 'Phase オプション追加後も option id を取得できません。')"
  fi

  printf 'Project の Phase に「%s」を追加しました。\n' "$want_name"
}

main() {
  require_cmd gh
  require_cmd jq
  check_gh_scope

  local proj_num
  proj_num="$(gh project list --owner "$ORG" --format json --limit 100 \
    | jq -r --arg t "$PROJECT_TITLE" '.projects[] | select(.title == $t) | .number' \
    | head -1)"
  [[ -n "$proj_num" && "$proj_num" != "null" ]] \
    || die "Project が見つかりません: owner=$ORG title=$PROJECT_TITLE"

  local project_id
  project_id="$(gh project view "$proj_num" --owner "$ORG" --format json | jq -r '.id')"
  [[ -n "$project_id" && "$project_id" != "null" ]] \
    || die "Project node id を取得できません (number=$proj_num)"

  ensure_github_phase_option "$project_id" "$PHASE_OPTION"
  local phase_field_id="${_gh_phase_field_id}"
  local phase_select_id="${_gh_phase_select_option_id}"

  for num in "${ISSUES[@]}"; do
    local url="https://github.com/${ORG}/${REPO}/issues/${num}"
    local item_id
    item_id="$(find_project_item_id "$proj_num" "$url" || true)"
    if [[ -z "$item_id" ]]; then
      printf 'adding %s\n' "$url"
      item_id="$(gh project item-add "$proj_num" --owner "$ORG" --url "$url" --format json | jq -r '.id')"
    else
      printf 'already on project: %s\n' "$url"
    fi
    [[ -n "$item_id" && "$item_id" != "null" ]] || die "item id が取得できません: $url"
    printf '  Phase -> %s\n' "$PHASE_OPTION"
    gh project item-edit --project-id "$project_id" --id "$item_id" \
      --field-id "$phase_field_id" --single-select-option-id "$phase_select_id"
  done

  printf '完了: Phase 5 issues (%s) を Project %s に同期しました。\n' "${ISSUES[*]}" "$proj_num"
}

main "$@"
