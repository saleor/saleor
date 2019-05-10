workflow "Linters" {
  on = "push"
  resolves = ["Black Linter", "Flake8 Linter"]
}

action "Build" {
  uses = "jefftriplett/python-actions@ba888adab5b57956dce82b7dfc06e87b65090a6d"
  args = "pip install flake8 black"
  env = {
    VENV_DIR = "/opt/"
  }
}

action "Black Linter" {
  uses = "jefftriplett/python-actions@ba888adab5b57956dce82b7dfc06e87b65090a6d"
  args = "black --check saleor tests"
  needs = ["Build"]
  env = {
    VENV_DIR = "/opt/"
  }
}

action "Flake8 Linter" {
  uses = "jefftriplett/python-actions@ba888adab5b57956dce82b7dfc06e87b65090a6d"
  args = "flake8 saleor tests"
  needs = ["Build"]
  env = {
    VENV_DIR = "/opt/"
  }
}
