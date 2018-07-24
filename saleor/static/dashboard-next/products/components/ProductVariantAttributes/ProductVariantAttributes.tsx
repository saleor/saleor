import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { AttributeType, AttributeValueType } from "../..";
import CardTitle from "../../../components/CardTitle";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductVariantAttributesProps {
  attributes?: Array<{
    attribute: AttributeType;
    value: AttributeValueType;
  }>;
  data: {
    [key: string]: {
      label: string;
      value: string;
    };
  };
  disabled: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  card: {
    overflow: "visible" as "visible"
  },
  grid: {
    "& input": {
      width: "100%"
    },
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr"
  }
}));

const ProductVariantAttributes = decorate<ProductVariantAttributesProps>(
  ({ attributes, classes, data, disabled, onChange }) => (
    <Card className={classes.card}>
      <CardTitle title={i18n.t("General Information")} />
      <CardContent className={classes.grid}>
        {attributes === undefined ? (
          <Skeleton />
        ) : attributes.length > 0 ? (
          attributes.map(item => {
            const { attribute } = item;
            return (
              <>
                <SingleAutocompleteSelectField
                  choices={
                    attribute.values
                      ? attribute.values.map(value => ({
                          label: value.name,
                          value: value.slug
                        }))
                      : []
                  }
                  disabled={disabled}
                  label={attribute.name}
                  name={attribute.slug}
                  value={data[attribute.slug]}
                  onChange={onChange}
                  custom
                  key={attribute.slug}
                />
                <div />
              </>
            );
          })
        ) : (
          <Typography>
            {i18n.t("This product type has no variant attributes.")}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
);
export default ProductVariantAttributes;
