# Maxwell MCP Tool Contract (v1)

## Unified Response Envelope

```json
{
  "ok": true,
  "code": "OK",
  "message": "success",
  "data": {}
}
```

Error example:

```json
{
  "ok": false,
  "code": "LICENSE_UNAVAILABLE",
  "message": "license server unreachable",
  "data": {
    "server": "1055@LAPTOP-DGVONA4D"
  }
}
```

---

## 1) health_check

- Purpose: verify paths/version/license basic availability.

Input:

```json
{
  "aedt_root": "D:\\Program Files\\AnsysEM\\v231\\Win64",
  "license_server": "1055@LAPTOP-DGVONA4D",
  "transport": "grpc"
}
```

Output data fields:
- `aedt_found` (bool)
- `version` (string)
- `license_reachable` (bool)
- `mode` (`implement_only` or `execute`)

---

## 2) open_or_create_project

- Purpose: open existing `.aedt` or create project/design skeleton.

Input:

```json
{
  "project_path": "results/maxwell-mcp/agv_wpt.aedt",
  "create_if_missing": true,
  "design_name": "AGV_WPT_Base"
}
```

Output data fields:
- `project_path`
- `design_name`
- `created` (bool)

---

## 3) set_design_variables

- Purpose: batch set design variables for geometry/electrical parameters.

Input:

```json
{
  "design_name": "AGV_WPT_Base",
  "variables": {
    "turns": "12",
    "coil_gap_cm": "6cm",
    "f_op": "85kHz"
  }
}
```

Output data fields:
- `updated_keys` (array)
- `skipped_keys` (array)

---

## 4) run_setup

- Purpose: run selected setup (if execution enabled).

Input:

```json
{
  "design_name": "AGV_WPT_Base",
  "setup_name": "Setup1",
  "allow_execute": false,
  "timeout_sec": 1800
}
```

Output data fields:
- `executed` (bool)
- `run_id` (string)
- `duration_sec` (number)

---

## 5) export_results

- Purpose: export L1/L2/M/k and report CSV to output directory.

Input:

```json
{
  "design_name": "AGV_WPT_Base",
  "output_dir": "results/maxwell-mcp",
  "exports": ["L1", "L2", "M", "k"]
}
```

Output data fields:
- `files` (array)
- `output_dir`

---

## Standard Error Codes

- `CONFIG_INVALID`
- `PATH_NOT_FOUND`
- `VERSION_UNSUPPORTED`
- `LICENSE_UNAVAILABLE`
- `SESSION_CREATE_FAILED`
- `SETUP_NOT_FOUND`
- `EXECUTION_DISABLED`
- `SOLVE_TIMEOUT`
- `EXPORT_FAILED`
