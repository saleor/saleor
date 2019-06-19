import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { Theme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import makeStyles from "@material-ui/styles/makeStyles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe, renderCollection, stopPropagation } from "../../../misc";
import { AttributeDetailsFragment_values } from "../../types/AttributeDetailsFragment";

export interface AttributeValuesProps {
  disabled: boolean;
  values: AttributeDetailsFragment_values[];
  onValueAdd: () => void;
  onValueDelete: (id: string) => void;
  onValueUpdate: (id: string) => void;
}

const useStyles = makeStyles((theme: Theme) => ({
  columnAdmin: {
    width: 300
  },
  columnStore: {
    width: 300
  },
  iconCell: {
    "&:last-child": {
      paddingRight: 0
    },
    width: 48 + theme.spacing.unit / 2
  },
  link: {
    cursor: "pointer"
  }
}));

const AttributeValues: React.FC<AttributeValuesProps> = ({
  disabled,
  onValueAdd,
  onValueDelete,
  onValueUpdate,
  values
}) => {
  const classes = useStyles({});

  return (
    <Card>
      <CardTitle
        title={i18n.t("Attribute Values")}
        toolbar={
          <Button color="primary" variant="text" onClick={onValueAdd}>
            {i18n.t("Add value", { context: "button" })}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.columnAdmin}>
              {i18n.t("Admin")}
            </TableCell>
            <TableCell className={classes.columnStore}>
              {i18n.t("Default Store View")}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            values
              ? values.sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
              : undefined,
            value => (
              <TableRow
                className={!!value ? classes.link : undefined}
                hover={!!value}
                onClick={!!value ? () => onValueUpdate(value.id) : undefined}
                key={maybe(() => value.id)}
              >
                <TableCell>
                  {maybe(() => value.slug) ? value.slug : <Skeleton />}
                </TableCell>
                <TableCell>
                  {maybe(() => value.name) ? value.name : <Skeleton />}
                </TableCell>
                <TableCell className={classes.iconCell}>
                  <IconButton
                    disabled={disabled}
                    onClick={stopPropagation(() => onValueDelete(value.id))}
                  >
                    <DeleteIcon color="primary" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>{i18n.t("No values found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
AttributeValues.displayName = "AttributeValues";
export default AttributeValues;
