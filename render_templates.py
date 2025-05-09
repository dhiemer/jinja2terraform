
import argparse
import os
import yaml
import shutil
import logging
import traceback
import sys
from pathlib import Path
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    UndefinedError,
    TemplateSyntaxError,
    TemplateNotFound,
)


def deep_merge(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value


def load_yaml_files(file_paths):
    merged = {}
    for path in file_paths:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
            deep_merge(merged, data)
    return merged


def render_templates(env, input_dir, output_dir, context):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    for path in Path(input_dir).rglob("*.j2"):
        rel_path = path.relative_to(input_dir)
        output_path = Path(output_dir) / rel_path.with_suffix("")

        os.makedirs(output_path.parent, exist_ok=True)

        try:
            template = env.get_template(str(rel_path))
            rendered = template.render(context)
        except TemplateNotFound as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[TEMPLATE NOT FOUND] Could not find template: {e.name}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            #traceback.print_exc(file=sys.stderr)
            continue
        except TemplateSyntaxError as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[SYNTAX ERROR] In file '{e.filename}', line {e.lineno}: {e.message}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            #traceback.print_exc(file=sys.stderr)
            continue
        except UndefinedError as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[MISSING VALUE] in file: [{rel_path}]. Likely missing variable in template.", file=sys.stderr)
            print(f"Jinja2 error: {str(e)}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            #traceback.print_exc(file=sys.stderr)
            continue
        except Exception as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[UNHANDLED ERROR] while rendering '{rel_path}': {e}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            continue

        with open(output_path, "w") as f:
            f.write(rendered)
        logging.info(f"Rendered: {rel_path} → {output_path}")


def inject_macros(env, macros_dir, context):
    if not os.path.isdir(macros_dir):
        return

    for macro_file in sorted(Path(macros_dir).glob("*.j2")):
        try:
            macro_template = env.get_template(str(macro_file.relative_to(macros_dir)))
            macro_module = macro_template.module
            for name in dir(macro_module):
                if not name.startswith("_"):
                    context[name] = getattr(macro_module, name)
        except Exception as e:
            print(f"[MACRO LOAD ERROR] Failed to load macro '{macro_file}': {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser(description="Render Jinja2 templates with merged YAML values and macros.")
    parser.add_argument("--value_base", nargs="+", required=True, help="Base YAML file(s) (lowest precedence)")
    parser.add_argument("--value_files", nargs="+", required=True, help="YAML file(s) to override base values")
    parser.add_argument("--target_files", required=True, help="Directory of Jinja2 template files to render")
    parser.add_argument("--macros_dir", default="macros", help="Directory containing Jinja2 macros (default: macros)")
    parser.add_argument("--output_yaml", default="combined_values.yaml", help="Path to save combined YAML file")
    parser.add_argument("--output_dir", default="rendered", help="Directory to save rendered templates")

    args = parser.parse_args()
    print("*************************************************************************************")
    logging.info("Loading and merging YAML values...")
    values = load_yaml_files(args.value_base)
    overrides = load_yaml_files(args.value_files)
    deep_merge(values, overrides)

    with open(args.output_yaml, "w") as f:
        yaml.dump(values, f, sort_keys=False)
    logging.info(f"Combined YAML written to [{args.output_yaml}]")

    env = Environment(
        loader=FileSystemLoader([args.target_files, args.macros_dir]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    inject_macros(env, args.macros_dir, values)

    logging.info(f"Rendering templates from [{args.target_files}]")
    render_templates(env, args.target_files, args.output_dir, values)

    print("*************************************************************************************")
    logging.info(f"Rendered yaml saved to       [{args.output_yaml}]")
    logging.info(f"Rendered templates saved to  [{args.output_dir}]")
    print("*************************************************************************************")


if __name__ == "__main__":
    main()

# cls ; python render_templates.py --value_base values/base1.yaml values/base2.yaml --value_files values/override1.yaml values/override2.yaml --target_files terraform --macros_dir macros --output_yaml .rendered/combined.yaml --output_dir .terraform_rendered 
