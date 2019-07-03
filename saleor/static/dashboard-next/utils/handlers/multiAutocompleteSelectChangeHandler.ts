import { MultiAutocompleteChoiceType } from "@saleor/components/MultiAutocompleteSelectField";
import { ChangeEvent, FormChange } from "@saleor/hooks/useForm";
import { toggle } from "../lists";

function createMultiAutocompleteSelectHandler(
  change: FormChange,
  setSelected: (choices: MultiAutocompleteChoiceType[]) => void,
  selected: MultiAutocompleteChoiceType[],
  choices: MultiAutocompleteChoiceType[]
): FormChange {
  return (event: ChangeEvent) => {
    change(event);

    const id = event.target.value;
    const choice = choices.find(choice => choice.value === id);

    setSelected(toggle(choice, selected, (a, b) => a.value === b.value));
  };
}

export default createMultiAutocompleteSelectHandler;
