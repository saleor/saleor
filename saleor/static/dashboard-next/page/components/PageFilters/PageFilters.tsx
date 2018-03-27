import TextField from "material-ui/TextField";
import * as React from "react";

import FilterCard from "../../../components/FilterCard";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";

interface PageFiltersState {
  title: string;
  url: string;
  debounceTimeout: any;
}

interface PageFiltersProps {
  formState?: {
    title: string;
    url: string;
  };
  handleClear();
  handleSubmit(formState: any);
}

export class PageFilters extends React.Component<
  PageFiltersProps,
  PageFiltersState
> {
  static defaultState = {
    title: "",
    url: ""
  };

  constructor(props) {
    super(props);
    this.state = { ...PageFilters.defaultState, ...props.formState };
  }

  render() {
    const { handleClear, handleSubmit } = this.props;
    const handleInputChange = event => {
      const { name, value } = event.target;
      const debounceTimeout = setTimeout(() => {
        handleSubmit({
          formData: { [name]: value }
        });
      }, 500);
      clearTimeout(this.state.debounceTimeout);
      this.setState({
        [name]: value,
        debounceTimeout
      });
    };

    const handleClearButtonClick = () => {
      this.setState(PageFilters.defaultState);
      handleClear();
    };
    return (
      <FilterCard handleClear={handleClearButtonClick}>
        <TextField
          fullWidth
          name="title"
          label={i18n.t("Title", {
            context: "Product filter field label"
          })}
          onChange={handleInputChange}
          value={this.state.title || ""}
        />
        <FormSpacer />
        <TextField
          fullWidth
          name="url"
          label={i18n.t("Url", {
            context: "Product filter field label"
          })}
          onChange={handleInputChange}
          value={this.state.url || ""}
        />
      </FilterCard>
    );
  }
}

export default PageFilters;
