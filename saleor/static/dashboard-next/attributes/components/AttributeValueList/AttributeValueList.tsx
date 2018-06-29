import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import AddIcon from "@material-ui/icons/Add";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";
import Skeleton from "../../../components/Skeleton";

import { EditableTableCell } from "../../../components/EditableTableCell/EditableTableCell";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface AttributeValueListProps {
  disabled: boolean;
  values: Array<{
    id: string;
    name: string;
    isNew?: boolean;
  }>;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles(theme => ({
  deleteIcon: {
    paddingLeft: 0,
    paddingRight: "0 !important",
    width: theme.spacing.unit * 7
  },
  edit: {
    width: "unset"
  },
  root: {
    marginTop: theme.spacing.unit * 2,
    overflow: "visible",
    [theme.breakpoints.down("md")]: {
      marginTop: theme.spacing.unit
    }
  }
}));
const AttributeValueList = decorate<AttributeValueListProps>(
  ({ classes, disabled, values, onChange }) => {
    const defaultValue = i18n.t("New value");
    const handleAdd = () =>
      onChange({
        target: {
          name: "values",
          value: [
            ...values,
            {
              id: "new-" + values.length,
              isNew: true,
              name: defaultValue
            }
          ]
        }
      } as any);
    const handleEdit = (id: string) => (name: string) =>
      onChange({
        target: {
          name: "values",
          value: values.map(v => (v.id === id ? { id, name } : v))
        }
      } as any);
    const handleDelete = (id: string) => () =>
      onChange({
        target: { name: "values", value: values.filter(v => v.id !== id) }
      } as any);
    return (
      <Card className={classes.root}>
        <PageHeader title={i18n.t("Attribute values")}>
          <IconButton disabled={disabled} onClick={handleAdd}>
            <AddIcon />
          </IconButton>
        </PageHeader>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{i18n.t("Name")}</TableCell>
              <TableCell className={classes.deleteIcon} />
            </TableRow>
          </TableHead>
          <TableBody>
            {values === undefined ? (
              <TableRow>
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
                  <EditableTableCell
                    classes={{ root: classes.edit }}
                    focused={value.isNew}
                    defaultValue={defaultValue}
                    value={value.name}
                    onConfirm={handleEdit(value.id)}
                  />
                  <TableCell className={classes.deleteIcon}>
                    <IconButton
                      disabled={disabled}
                      onClick={handleDelete(value.id)}
                    >
                      <CloseIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("No attribute values found")}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    );
  }
);
AttributeValueList.displayName = "AttributeValueList";
export default AttributeValueList;
