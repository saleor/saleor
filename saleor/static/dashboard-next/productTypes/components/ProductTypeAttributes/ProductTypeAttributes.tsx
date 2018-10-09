import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { AttributeTypeEnum } from "../../../types/globalTypes";
import {
  ProductTypeDetails_productType_productAttributes,
  ProductTypeDetails_productType_variantAttributes
} from "../../types/ProductTypeDetails";
import ProductTypeAttributeEditDialog, {
  FormData as ProductTypeAttributeEditDialogFormData
} from "../ProductTypeAttributeEditDialog/ProductTypeAttributeEditDialog";

interface ProductTypeAttributesProps {
  attributes:
    | ProductTypeDetails_productType_productAttributes[]
    | ProductTypeDetails_productType_variantAttributes[];
  type: AttributeTypeEnum;
  onAttributeAdd: (
    data: ProductTypeAttributeEditDialogFormData,
    type: AttributeTypeEnum
  ) => void;
  onAttributeDelete: (id: string, event: React.MouseEvent<any>) => void;
  onAttributeUpdate: (
    id: string,
    data: ProductTypeAttributeEditDialogFormData
  ) => void;
}

const decorate = withStyles(theme => ({
  iconCell: {
    "&:last-child": {
      paddingRight: 0
    },
    width: 48 + theme.spacing.unit / 2
  },
  link: {
    cursor: "pointer" as "pointer"
  },
  textLeft: {
    textAlign: "left" as "left"
  }
}));
const ProductTypeAttributes = decorate<ProductTypeAttributesProps>(
  ({
    attributes,
    classes,
    type,
    onAttributeAdd,
    onAttributeDelete,
    onAttributeUpdate
  }) => (
    <Toggle>
      {(openedAttributeAddDialog, { toggle: toggleAttributeAddDialog }) => (
        <>
          <Card>
            <CardTitle
              title={
                type === AttributeTypeEnum.PRODUCT
                  ? i18n.t("Product Attributes")
                  : i18n.t("Variant Attributes")
              }
              toolbar={
                <Button
                  color="secondary"
                  variant="flat"
                  onClick={toggleAttributeAddDialog}
                >
                  {i18n.t("Add attribute", { context: "button" })}
                </Button>
              }
            />
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{i18n.t("Attribute name")}</TableCell>
                  <TableCell className={classes.textLeft}>
                    {i18n.t("Values")}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {renderCollection(
                  attributes,
                  attribute => (
                    <Toggle key={maybe(() => attribute.id)}>
                      {(
                        openedAttributeEditDialog,
                        { toggle: toggleAttributeEditDialog }
                      ) => (
                        <>
                          <TableRow
                            className={!!attribute ? classes.link : undefined}
                            hover={!!attribute}
                            onClick={toggleAttributeEditDialog}
                            key={maybe(() => attribute.id)}
                          >
                            <TableCell>
                              {maybe(() => attribute.name) ? (
                                attribute.name
                              ) : (
                                <Skeleton />
                              )}
                            </TableCell>
                            <TableCell className={classes.textLeft}>
                              {maybe(() => attribute.values) !== undefined ? (
                                attribute.values
                                  .map(value => value.name)
                                  .join(", ")
                              ) : (
                                <Skeleton />
                              )}
                            </TableCell>
                            <TableCell className={classes.iconCell}>
                              <IconButton
                                onClick={event =>
                                  onAttributeDelete(attribute.id, event)
                                }
                              >
                                <DeleteIcon color="secondary" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                          <ProductTypeAttributeEditDialog
                            name={maybe(() => attribute.name)}
                            opened={openedAttributeEditDialog}
                            title={i18n.t("Edit attribute")}
                            values={maybe(() =>
                              attribute.values.map(value => ({
                                label: value.name,
                                value: value.id
                              }))
                            )}
                            onClose={toggleAttributeEditDialog}
                            onConfirm={data =>
                              onAttributeUpdate(attribute.id, data)
                            }
                          />
                        </>
                      )}
                    </Toggle>
                  ),
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
          <ProductTypeAttributeEditDialog
            opened={openedAttributeAddDialog}
            title={i18n.t("Add attribute")}
            name=""
            values={[]}
            onClose={toggleAttributeAddDialog}
            onConfirm={data => onAttributeAdd(data, type)}
          />
        </>
      )}
    </Toggle>
  )
);
ProductTypeAttributes.displayName = "ProductTypeAttributes";
export default ProductTypeAttributes;
