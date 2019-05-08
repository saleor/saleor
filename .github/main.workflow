workflow "Linters" {
  on = "push"
  resolves = ["Black Linter"]
}

action "Black Linter" {
  uses = "lgeiger/black-action@4379f39aa4b6a3bb1cceb46a7665b9c26647d82d"
  args = ". --check"
}
