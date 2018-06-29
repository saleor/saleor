import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import CloseIcon from "@material-ui/icons/Close";
import ReorderIcon from "@material-ui/icons/Reorder";
import * as React from "react";
import { SortableContainer, SortableElement } from "react-sortable-hoc";
import Skeleton from "../../../components/Skeleton";

import { EditableTableCell } from "../../../components/EditableTableCell/EditableTableCell";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface AttributeValueListProps {
  disabled: boolean;
  values: Array<{
    id: string;
    name: string;
    sortOrder: number;
    slug: string;
  }>;
  onAdd: () => void;
  onDelete: (id: string) => () => void;
  onEdit: (id: string) => (name: string) => () => void;
  onReorder: (event: { oldIndex: number; newIndex: number }) => void;
}

const decorate = withStyles(theme => ({
  deleteIcon: {
    paddingLeft: 0,
    paddingRight: "0 !important",
    width: theme.spacing.unit * 7
  },
  reorderIcon: {
    cursor: "move" as "move",
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: 0,
    width: theme.spacing.unit * 9
  },
  root: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: { marginTop: theme.spacing.unit }
  }
}));
const AttributeValueList = decorate<AttributeValueListProps>(
  ({ classes, disabled, values, onAdd, onDelete, onEdit, onReorder }) => (
    <Card className={classes.root}>
      <PageHeader title={i18n.t("Attribute values")}>
        <IconButton disabled={disabled} onClick={onAdd}>
          <AddIcon />
        </IconButton>
      </PageHeader>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.reorderIcon} />
            <TableCell>{i18n.t("Name")}</TableCell>
            <TableCell className={classes.deleteIcon} />
          </TableRow>
        </TableHead>
        <TableBody>
          {values === undefined ? (
            <TableRow>
              <TableCell className={classes.reorderIcon}>
                <ReorderIcon />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell className={classes.deleteIcon}>
                <IconButton disabled={disabled}>
                  <CloseIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ) : values.length > 0 ? (
            values.map(value => (
              <TableRow>
                <TableCell className={classes.reorderIcon}>
                  <ReorderIcon />
                </TableCell>
                <EditableTableCell
                  value={value.name}
                  onConfirm={onEdit(value.id)}
                />
                <TableCell className={classes.deleteIcon}>
                  <IconButton disabled={disabled} onClick={onDelete(value.id)}>
                    <CloseIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>
                {i18n.t("No attribute values found")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
AttributeValueList.displayName = "AttributeValueList";
export default AttributeValueList;
