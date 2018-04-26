import Card, { CardContent } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductAttributesFormProps {
  // TODO: type when API blah blah blah
  attributes?: any[];
  productAttributes?: any[];
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({}));
export const ProductAttributesForm = decorate<ProductAttributesFormProps>(
  ({ classes, attributes, productAttributes, loading, onChange }) => {
    if (loading) {
      return (
        <Card>
          <PageHeader title={i18n.t("Attributes")} />
          <CardContent>
            <Skeleton />
          </CardContent>
        </Card>
      );
    }
    const keyedAttributes = attributes.reduce((prev, curr) => {
      prev[curr.slug] = curr;
      return prev;
    }, {});
    const keyedProductAttributes = productAttributes.reduce((prev, curr) => {
      prev[curr.name] = curr.value;
      return prev;
    }, {});
    return (
      <Card>
        <PageHeader title={i18n.t("Attributes")} />
        <CardContent>
          {attributes.map((attribute, index) => (
            <React.Fragment key={index}>
              <SingleSelectField
                name={attribute.slug}
                label={attribute.name}
                onChange={onChange}
                value={
                  keyedAttributes[attribute.slug].values.filter(
                    attr => attr.slug === keyedProductAttributes[attribute.slug]
                  )[0].slug
                }
                choices={attribute.values.map(choice => ({
                  label: choice.name,
                  value: choice.slug
                }))}
                key={index}
              />
              <FormSpacer />
            </React.Fragment>
          ))}
        </CardContent>
      </Card>
    );
  }
);
export default ProductAttributesForm;
