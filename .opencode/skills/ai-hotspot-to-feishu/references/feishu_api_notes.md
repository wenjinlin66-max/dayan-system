# 飞书 API 说明（本 skill 使用）

## 鉴权

- `POST /open-apis/auth/v3/tenant_access_token/internal`

## wiki -> docx 解析

- `GET /open-apis/wiki/v2/spaces/get_node?token={wiki_token}`

当用户提供 wiki 链接时，先通过该接口拿到 `obj_type` 和 `obj_token`。
仅当 `obj_type=docx` 时继续写入。

## docx 追加块

- `POST /open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children`

本脚本默认将 `block_id` 设为 `document_id`，在根节点末尾追加。
