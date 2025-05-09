# Jinja2 + YAML Terraform Renderer

This project is a flexible, macro-enabled Terraform templating engine using **Jinja2** and **YAML**, designed to be a powerful alternative to Terragrunt for personal or professional infrastructure-as-code projects.

## ✅ What It Does

- Deep-merges multiple YAML configuration files
- Renders `.j2` templates into Terraform-ready `.tf` files
- Supports reusable logic via Jinja2 macros
- Encourages DRY configuration with base + overrides
- Outputs:
  - `combined_values.yaml`: merged config file
  - `terraform_rendered/`: rendered files

## 🆚 Comparison to Terragrunt

| Feature                        | Jinja2 Project              | Terragrunt                  |
|-------------------------------|-----------------------------|-----------------------------|
| DRY Config                    | ✅ YAML layering            | ✅ HCL locals                |
| Macros & Logic                | ✅ Jinja2 macros/functions  | ❌ None                     |
| File Types Supported          | ✅ Any (TF, shell, docs)    | ❌ Only Terraform           |
| State Backend Injection       | ❌ Planned                  | ✅ Automatic                 |
| Dependency Graph              | ❌ Planned                  | ✅ Built-in                  |
| Plan/Apply Wrapping           | ❌ Manual or TODO           | ✅ `plan-all`, `apply-all`   |

## 🔧 How to Use

```bash
python render_templates.py \
  --value_base values/base.yaml \
  --value_files values/dev.yaml \
  --target_files terraform \
  --macros_dir macros \
  --output_yaml combined.yaml \
  --output_dir terraform_rendered
```

Then you can `cd terraform_rendered/` and run:

```bash
terraform init
terraform plan
terraform apply
```

## 🚧 Pending Enhancements

- [ ] Inject Terraform remote state blocks
- [ ] Implement dependency graph support (apply ordering)
- [ ] Add `terraform plan` / `apply` orchestration in Python
- [ ] Optional: YAML schema validation
- [ ] Optional: Auto-lint rendered files

