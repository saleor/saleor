import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import i18n from "@saleor/i18n";
import { maybe, renderCollection, stopPropagation } from "@saleor/misc";
import { ListActions } from "@saleor/types";
import { AttributeTypeEnum } from "@saleor/types/globalTypes";
import {
  ProductTypeDetails_productType_productAttributes,
  ProductTypeDetails_productType_variantAttributes
} from "../../types/ProductTypeDetails";

const styles = (theme: Theme) =>
  createStyles({
    iconCell: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    link: {
      cursor: "pointer"
    },
    textLeft: {
      textAlign: "left"
    }
  });

interface ProductTypeAttributesProps extends ListActions {
  attributes:
    | ProductTypeDetails_productType_productAttributes[]
    | ProductTypeDetails_productType_variantAttributes[];
  disabled: boolean;
  type: string;
  onAttributeAssign: (type: AttributeTypeEnum) => void;
  onAttributeClick: (id: string) => void;
  onAttributeUnassign: (id: string) => void;
}

const ProductTypeAttributes = withStyles(styles, {
  name: "ProductTypeAttributes"
})(
  ({
    attributes,
    classes,
    disabled,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar,
    type,
    onAttributeAssign,
    onAttributeClick,
    onAttributeUnassign
  }: ProductTypeAttributesProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        title={
          type === AttributeTypeEnum.PRODUCT
            ? i18n.t("Product Attributes")
            : i18n.t("Variant Attributes")
        }
        toolbar={
          <Button
            color="primary"
            variant="text"
            onClick={() => onAttributeAssign(AttributeTypeEnum[type])}
          >
            {i18n.t("Assign attribute", { context: "button" })}
          </Button>
        }
      />
      <Table>
        <TableHead
          disabled={disabled}
          selected={selected}
          items={attributes}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell>{i18n.t("Attribute name")}</TableCell>
          <TableCell />
        </TableHead>
        <TableBody>
          {renderCollection(
            attributes,
            attribute => {
              const isSelected = attribute ? isChecked(attribute.id) : false;

              return (
                <TableRow
                  selected={isSelected}
                  className={!!attribute ? classes.link : undefined}
                  hover={!!attribute}
                  onClick={
                    !!attribute
                      ? () => onAttributeClick(attribute.id)
                      : undefined
                  }
                  key={maybe(() => attribute.id)}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(attribute.id)}
                    />
                  </TableCell>
                  <TableCell>
                    {maybe(() => attribute.name) ? (
                      attribute.name
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.iconCell}>
                    <IconButton
                      onClick={stopPropagation(() =>
                        onAttributeUnassign(attribute.id)
                      )}
                    >
                      <DeleteIcon color="primary" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("No attributes found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductTypeAttributes.displayName = "ProductTypeAttributes";
export default ProductTypeAttributes;
