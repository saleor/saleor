import * as React from "react";
import TextField from "material-ui/TextField";
import { Component } from "react";

import FilterCard from "../../components/cards/FilterCard";
import FormSpacer from "../../components/FormSpacer";
import MultiSelectField from "../../components/MultiSelectField";
import SingleSelectField from "../../components/SingleSelectField";
import PriceField from "../../components/PriceField";
import i18n from "../../i18n";

interface ProductFiltersState {
  highlighted: string;
  name: string;
  price_min: string;
  price_max: string;
  productTypes: Array<string>;
  published: string;
}
interface ProductFiltersProps {
  productTypes: Array<{
    id: string;
    name: string;
  }>;
  formState?: ProductFiltersState;
  handleSubmit(formState: any);
  handleClear();
}

export class ProductFilters extends Component<
  ProductFiltersProps,
  ProductFiltersState
> {
  static defaultState = {
    highlighted: "",
    name: "",
    price_min: "",
    price_max: "",
    productTypes: [],
    published: ""
  };

  constructor(props) {
    super(props);
    this.state = {
      ...ProductFilters.defaultState,
      ...props.formState
    };
  }

  componentWillReceiveProps(nextProps) {
    this.setState({ ...ProductFilters.defaultState, ...nextProps.formState });
  }

  handleInputChange = event => {
    this.setState({ [event.target.name]: event.target.value });
  };

  render() {
    const { handleSubmit, productTypes, handleClear } = this.props;
    const publishingStatuses = [
      {
        label: i18n.t("Published", { context: "Product publishing status" }),
        value: "1"
      },
      {
        label: i18n.t("Not published", {
          context: "Product publishing status"
        }),
        value: "0"
      },
      {
        label: i18n.t("All", {
          context: "Product publishing status"
        }),
        value: ""
      }
    ];
    const highlightingStatuses = [
      {
        label: i18n.t("Highlighted", {
          context: "Product highlighting status"
        }),
        value: "1"
      },
      {
        label: i18n.t("Not highlighted", {
          context: "Product highlighting status"
        }),
        value: "0"
      },
      {
        label: i18n.t("All", {
          context: "Product highlighting status"
        }),
        value: ""
      }
    ];

    return (
      <FilterCard
        handleClear={handleClear}
        handleSubmit={handleSubmit(this.state)}
      >
        <TextField
          fullWidth
          name="name"
          label={i18n.t("Name", {
            context: "Product filter field label"
          })}
          onChange={this.handleInputChange}
          value={this.state.name}
        />
        <FormSpacer>
          <MultiSelectField
            label={i18n.t("Product type", {
              context: "Product filter field label"
            })}
            choices={productTypes.map(type => ({
              value: type.id,
              label: type.name
            }))}
            name="productTypes"
            onChange={this.handleInputChange}
            value={this.state.productTypes}
          />
        </FormSpacer>
        <FormSpacer>
          <PriceField
            currencySymbol="USD"
            label={i18n.t("Price")}
            name="price"
            onChange={this.handleInputChange}
            value={{ min: this.state.price_min, max: this.state.price_max }}
          />
        </FormSpacer>
        <FormSpacer>
          <SingleSelectField
            label={i18n.t("Published", {
              context: "Product filter field label"
            })}
            choices={publishingStatuses}
            name="published"
            onChange={this.handleInputChange}
            value={this.state.published}
          />
        </FormSpacer>
        <FormSpacer>
          <SingleSelectField
            label={i18n.t("Highlighted", {
              context: "Product filter field label"
            })}
            choices={highlightingStatuses}
            name="highlighted"
            onChange={this.handleInputChange}
            value={this.state.highlighted}
          />
        </FormSpacer>
      </FilterCard>
    );
  }
}

export default ProductFilters;
