def load_template(template_name):
    with open(f"prompts/{template_name}", "r") as file:
        return file.read()
