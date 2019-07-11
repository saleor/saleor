import "./scss/index.scss";

import classNames from "classnames";
import { filter, find } from "lodash";
import * as React from "react";

import { useClickedOutside } from "../../hooks";
import {
  IFilteredListArgs,
  ISelectChange,
  ISelectItem,
  ISelectProps
} from "./customTypes";
import SelectOptionsList from "./SelectOptionsList";

const updateOptions = (
  { label, value }: ISelectItem,
  onChange: ISelectChange
) => onChange({ country: label, code: value });

const filterList = ({ searchPhrase, options }: IFilteredListArgs) =>
  filter(options, ({ label }) =>
    label.toLowerCase().includes(searchPhrase.toLowerCase())
  );

const isAutofilled = (inputValue: string, newInputValue: string) =>
  newInputValue.length > 1 &&
  newInputValue.substring(0, newInputValue.length - 1) !== inputValue;

const findAutofilledOption = (options: ISelectItem[], inputValue: string) =>
  find(
    options,
    ({ label }) => label.toLowerCase() === inputValue.toLowerCase()
  );

export const Select = (props: ISelectProps) => {
  const {
    autoComplete,
    defaultValue = { label: "", value: "" },
    label,
    onChange,
    options,
    name,
  } = props;
  const [open, setOpen] = React.useState(false);
  const [searchPhrase, setSearchPhrase] = React.useState(defaultValue.label);
  const { clickedOutside, setElementRef } = useClickedOutside();
  const inputRef = React.useRef<HTMLInputElement>(null);
  const activeOptionRef = React.useRef<HTMLParagraphElement>(null);

  const resetInputValueToDefault = () => setSearchPhrase(defaultValue.label);

  React.useEffect(() => {
    resetInputValueToDefault();
  }, [clickedOutside, defaultValue]);

  React.useEffect(() => {
    if (activeOptionRef.current && open) {
      activeOptionRef.current.scrollIntoView();
      activeOptionRef.current.focus();
    }
  }, [open]);

  const shouldOpen = clickedOutside ? false : open;
  const shouldSearch = defaultValue.label !== searchPhrase;

  const renderLabel = (label?: string) =>
    label && <label className="input__label">{label}</label>;

  const changeSelectionRange = (e: React.ChangeEvent<any>) =>
    inputRef.current.setSelectionRange(0, e.target.value.length);

  return (
    <div
      ref={setElementRef()}
      className={classNames("react-select select", {
        "select--open": shouldOpen,
      })}
    >
      <input
        className="select__hidden"
        autoComplete={autoComplete}
        name={name}
        defaultValue={defaultValue.value}
      />
      <div className="select__container">
        <div className="select__title">
          <input
            ref={inputRef}
            className="input__field"
            value={searchPhrase}
            onChange={e => {
              const { value } = e.target;
              setSearchPhrase(value);
              if (isAutofilled(searchPhrase, value)) {
                const country = findAutofilledOption(options, value);
                return country && updateOptions(country, onChange);
              }
            }}
            onClick={e => {
              changeSelectionRange(e);
              if (open) {
                resetInputValueToDefault();
              }
              setOpen(!open);
            }}
          />
          {renderLabel(label)}
        </div>

        <div
          className={classNames("select__options", {
            "select__options--open": shouldOpen,
          })}
        >
          <SelectOptionsList
            ref={activeOptionRef}
            activeOption={defaultValue}
            options={
              shouldSearch ? filterList({ searchPhrase, options }) : options
            }
            onChange={onChange}
            setOpen={setOpen}
            updateOptions={updateOptions}
          />
        </div>
      </div>
    </div>
  );
};

export default Select;
