import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { debug } from "util";
import { AttributeType, AttributeValueType } from "../..";
import PageHeader from "../../../components/PageHeader";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductVariantAttributesProps {
  attributes?: Array<{
    attribute: AttributeType;
    value: AttributeValueType;
  }>;
  data: {
    [key: string]: string;
  };
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  grid: {
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr",
    "& input": {
      width: "100%"
    }
  }
}));

const ProductVariantAttributes = decorate<ProductVariantAttributesProps>(
  ({ attributes, classes, data, loading, onChange }) => (
    <Card>
      <PageHeader title={i18n.t("Attributes")} />
      <CardContent className={classes.grid}>
        {attributes ? (
          attributes.map(item => {
            const { attribute } = item;
            return (
              <SingleSelectField
                choices={
                  attribute.values
                    ? attribute.values.map(value => ({
                        label: value.name,
                        value: value.slug
                      }))
                    : []
                }
                onChange={onChange}
                value={data[attribute.slug]}
                label={attribute.name}
                name={attribute.slug}
                key={attribute.slug}
              />
            );
          })
        ) : (
          <Skeleton />
        )}
      </CardContent>
    </Card>
  )
);
export default ProductVariantAttributes;
