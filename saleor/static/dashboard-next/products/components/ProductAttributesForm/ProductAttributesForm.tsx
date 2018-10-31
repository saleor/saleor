import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AttributeType, AttributeValueType } from "../..";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface AttributesFormProps {
  attributes?: Array<{
    attribute: AttributeType;
    value: AttributeValueType;
  }>;
  data?: {
    [key: string]: any;
  };
  disabled?: boolean;
  onChange(event: any);
}

export const AttributesForm: React.StatelessComponent<
  AttributesFormProps
> = ({ attributes, data, disabled, onChange }) => (
  <Card>
    <PageHeader title={i18n.t("Attributes")} />
    <CardContent>
      {attributes ? (
        attributes.map((item, index) => (
          <React.Fragment key={index}>
            <SingleSelectField
              disabled={disabled}
              name={item.attribute.slug}
              label={item.attribute.name}
              onChange={onChange}
              value={data[item.attribute.slug]}
              choices={item.attribute.values.map(choice => ({
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
);
AttributesForm.displayName = "AttributesForm";
export default AttributesForm;
