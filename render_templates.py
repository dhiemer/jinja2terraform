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
from glob import glob


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
        if "macros" in path.parts:
            continue  # Skip rendering macro files
        rel_path = path.relative_to(input_dir)
        output_path = Path(output_dir) / rel_path.with_suffix("")

        os.makedirs(output_path.parent, exist_ok=True)

        try:
            template = env.get_template(rel_path.as_posix())
            rendered = template.render(context)
        except TemplateNotFound as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[TEMPLATE NOT FOUND] Could not find template: {e.name}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            continue
        except TemplateSyntaxError as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[SYNTAX ERROR] In file '{e.filename}', line {e.lineno}: {e.message}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
            continue
        except UndefinedError as e:
            print("*************************************************************************************", file=sys.stderr)
            print(f"[MISSING VALUE] in file: [{rel_path}]. Likely missing variable in template.", file=sys.stderr)
            print(f"Jinja2 error: {str(e)}", file=sys.stderr)
            print("*************************************************************************************", file=sys.stderr)
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
    loader_root = "terraform"

    for macro_file in sorted(Path(macros_dir).glob("*.j2")):
        try:
            macro_template = env.get_template(macro_file.relative_to(loader_root).as_posix())
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
    parser.add_argument("--environment", required=True, help="Environment to deploy (e.g. dev, prod)")
    parser.add_argument("--target_files", default="terraform", help="Directory to files to render")
    parser.add_argument("--macros_dir", default="terraform/macros", help="Directory containing Jinja2 macros")
    parser.add_argument("--output_yaml", default=".output/.rendered/combined.yaml", help="Path to save combined YAML file")
    parser.add_argument("--output_dir", default=".output/.terraform_rendered", help="Directory to save rendered templates")

    args = parser.parse_args()
    print("\n\n")
    print("     ██╗██╗███╗   ██╗     ██╗ █████╗ ██████╗ ████████╗███████╗██████╗ ██████╗  █████╗ ███████╗ ██████╗ ██████╗ ███╗   ███╗   ")
    print("     ██║██║████╗  ██║     ██║██╔══██╗╚════██╗╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗████╗ ████║   ")
    print("     ██║██║██╔██╗ ██║     ██║███████║ █████╔╝   ██║   █████╗  ██████╔╝██████╔╝███████║█████╗  ██║   ██║██████╔╝██╔████╔██║   ")
    print("██   ██║██║██║╚██╗██║██   ██║██╔══██║██╔═══╝    ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║   ")
    print("╚█████╔╝██║██║ ╚████║╚█████╔╝██║  ██║███████╗   ██║   ███████╗██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║   ")
    print(" ╚════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝   \n\n")


    env_files = f"environments/{args.environment}"
    if not os.path.isdir(env_files):
        print(f"[ERROR] Target template directory does not exist: {env_files}", file=sys.stderr)
        sys.exit(1)

    logging.info("Get Core yaml files [environments]")
    core_yaml_files = sorted(glob(os.path.join("environments", "*.yml")) + glob(os.path.join("environments", "*.yaml")))
    if not core_yaml_files:
        print(f"[ERROR] No YAML files found in environments/", file=sys.stderr)
        sys.exit(1)

    logging.info(f"Get Envionment yaml files[{env_files}]")
    env_yaml_files = sorted(glob(os.path.join(env_files, "*.yml")) + glob(os.path.join(env_files, "*.yaml")))
    if not env_yaml_files:
        print(f"[ERROR] No YAML files found in {env_files}", file=sys.stderr)
        sys.exit(1)

    logging.info(f"Target Environment Set [{args.environment}] [{env_files}]")

    logging.info(f"Loading [{core_yaml_files}] [{env_yaml_files}]")
    core_values = load_yaml_files(core_yaml_files)
    env_values = load_yaml_files(env_yaml_files)

    logging.info(f"Merging...")
    deep_merge(core_values, env_values)

    with open(args.output_yaml, "w") as f:
        yaml.dump(core_values, f, sort_keys=False)
    logging.info(f"Combined YAML written to [{args.output_yaml}]")

    env = Environment(
        loader=FileSystemLoader("terraform"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    inject_macros(env, args.macros_dir, core_values)
    print("*************************************************************************************")
    logging.info(f"Rendering templates from [{args.target_files}]")
    print("*************************************************************************************")
    render_templates(env, args.target_files, args.output_dir, core_values)
    print("*************************************************************************************")
    logging.info(f"Rendered yaml saved to       [{args.output_yaml}]")
    logging.info(f"Rendered templates saved to  [{args.output_dir}]")
    print("*************************************************************************************")
    print("Everything is Awesome! \n\n")


if __name__ == "__main__":
    main()


# cls ; python render_templates.py --environment dev 