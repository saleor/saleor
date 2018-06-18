import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AttributeType } from "../..";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductAttributesFormProps {
  attributes?: Array<{
    attribute: AttributeType & {
      values: AttributeType[];
    };
    value: AttributeType;
  }>;
  data: any;
  disabled?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({}));
export const ProductAttributesForm = decorate<ProductAttributesFormProps>(
  ({ classes, attributes, data, disabled, onChange }) => (
    <Card>
      <PageHeader title={i18n.t("Attributes")} />
      <CardContent>
        {attributes ? (
          attributes.map((attribute, index) => (
            <React.Fragment key={index}>
              <SingleSelectField
                disabled={disabled}
                name={attribute.attribute.slug}
                label={attribute.attribute.name}
                onChange={onChange}
                value={data[attribute.attribute.slug]}
                choices={attribute.attribute.values.map(choice => ({
                  label: choice.name,
                  value: choice.slug
                }))}
                key={index}
              />
              <FormSpacer />
            </React.Fragment>
          ))
        ) : (
          <Skeleton />
        )}
      </CardContent>
    </Card>
  )
);
export default ProductAttributesForm;
