import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { Theme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import makeStyles from "@material-ui/styles/makeStyles";
import React from "react";
import { SortableElement } from "react-sortable-hoc";

import CardTitle from "@saleor/components/CardTitle";
import Skeleton from "@saleor/components/Skeleton";
import {
  SortableTableBody,
  SortableTableRow
} from "@saleor/components/SortableTable";
import i18n from "@saleor/i18n";
import Draggable from "@saleor/icons/Draggable";
import { maybe, renderCollection, stopPropagation } from "@saleor/misc";
import { ReorderEvent } from "@saleor/types";
import { AttributeDetailsFragment_values } from "../../types/AttributeDetailsFragment";

export interface AttributeValuesProps {
  disabled: boolean;
  values: AttributeDetailsFragment_values[];
  onValueAdd: () => void;
  onValueDelete: (id: string) => void;
  onValueReorder: ReorderEvent;
  onValueUpdate: (id: string) => void;
}

const useStyles = makeStyles((theme: Theme) => ({
  columnAdmin: {
    width: "50%"
  },
  columnDrag: {
    width: 48 + theme.spacing.unit * 1.5
  },
  columnStore: {
    width: "50%"
  },
  dragIcon: {
    cursor: "grab"
  },
  ghost: {
    "& td": {
      borderBottom: "none"
    },
    background: theme.palette.background.paper,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.overrides.MuiTableCell.root.fontSize,
    opacity: 0.5
  },
  iconCell: {
    "&:last-child": {
      paddingRight: theme.spacing.unit
    },
    width: 48 + theme.spacing.unit * 1.5
  },
  link: {
    cursor: "pointer"
  }
}));

const AttributeValues: React.FC<AttributeValuesProps> = ({
  disabled,
  onValueAdd,
  onValueDelete,
  onValueReorder,
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
            <TableCell className={classes.columnDrag} />
            <TableCell className={classes.columnAdmin}>
              {i18n.t("Admin")}
            </TableCell>
            <TableCell className={classes.columnStore}>
              {i18n.t("Default Store View")}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <SortableTableBody
          helperClass={classes.ghost}
          axis="y"
          lockAxis="y"
          onSortEnd={onValueReorder}
        >
          {renderCollection(
            values
              ? values.sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
              : undefined,
            (value, valueIndex) => (
              <SortableTableRow
                className={!!value ? classes.link : undefined}
                hover={!!value}
                onClick={!!value ? () => onValueUpdate(value.id) : undefined}
                key={maybe(() => value.id)}
                index={valueIndex}
              >
                <TableCell className={classes.columnAdmin}>
                  {maybe(() => value.slug) ? value.slug : <Skeleton />}
                </TableCell>
                <TableCell className={classes.columnStore}>
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
              </SortableTableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>{i18n.t("No values found")}</TableCell>
              </TableRow>
            )
          )}
        </SortableTableBody>
      </Table>
    </Card>
  );
};
AttributeValues.displayName = "AttributeValues";
export default AttributeValues;
