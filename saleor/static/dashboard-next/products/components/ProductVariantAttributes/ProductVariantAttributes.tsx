import Card, { CardContent } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductVariantAttributesProps {
  attributes?: Array<{
    value: string;
    attribute: {
      slug: string;
      name: string;
      values: string[];
    };
  }>;
  formData?: any;
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
  ({ attributes, classes, formData, loading, onChange }) => (
    <Card>
      <PageHeader title={i18n.t("Attributes")} />
      <CardContent className={classes.grid}>
        {loading ? (
          <Skeleton />
        ) : (
          attributes.map(attribute => (
            <SingleSelectField
              choices={attribute.attribute.values.map(attr => ({
                label: attr,
                value: attr
              }))}
              onChange={onChange}
              value={formData ? formData[attribute.attribute.slug] : ""}
              label={attribute.attribute.name}
              name={attribute.attribute.slug}
              key={attribute.attribute.slug}
            />
          ))
        )}
      </CardContent>
    </Card>
  )
);
export default ProductVariantAttributes;
