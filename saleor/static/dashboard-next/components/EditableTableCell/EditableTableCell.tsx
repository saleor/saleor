import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import TextField, { TextFieldProps } from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import Form from "../../components/Form";
import Toggle from "../../components/Toggle";

interface EditableTableCellProps {
  className?: string;
  defaultValue?: string;
  focused?: boolean;
  InputProps?: TextFieldProps;
  value: string;
  onConfirm(value: string): any;
}

const decorate = withStyles(theme => ({
  container: {
    position: "relative" as "relative"
  },
  overlay: {
    cursor: "pointer",
    height: "100vh",
    left: 0,
    position: "fixed" as "fixed",
    top: 0,
    width: "100vw",
    zIndex: 1
  },
  root: {
    left: 0,
    minWidth: theme.spacing.unit * 20,
    position: "absolute" as "absolute",
    top: 0,
    width: `calc(100% + ${4 * theme.spacing.unit}px)`,
    zIndex: 2
  },
  text: {
    cursor: "pointer",
    fontSize: "0.8125rem"
  }
}));
export const EditableTableCell = decorate<EditableTableCellProps>(
  ({
    classes,
    className,
    defaultValue,
    focused,
    InputProps,
    value,
    onConfirm
  }) => (
    <TableCell className={classNames(classes.container, className)}>
      <Toggle initial={focused}>
        {(opened, { enable, disable }) => {
          const handleConfirm = (data: { value: string }) => {
            disable();
            onConfirm(data.value);
          };
          return (
            <>
              {opened && <div className={classes.overlay} onClick={disable} />}
              <Form
                initial={{ value }}
                onSubmit={handleConfirm}
                useForm={false}
              >
                {({ change, data }) => (
                  <>
                    <Typography
                      variant="caption"
                      onClick={enable}
                      className={classes.text}
                    >
                      {value || defaultValue}
                    </Typography>
                    {opened && (
                      <div className={classes.root}>
                        <Card>
                          <CardContent>
                            <TextField
                              name="value"
                              autoFocus
                              fullWidth
                              onChange={change}
                              value={data.value}
                              {...InputProps}
                            />
                          </CardContent>
                        </Card>
                      </div>
                    )}
                  </>
                )}
              </Form>
            </>
          );
        }}
      </Toggle>
    </TableCell>
  )
);
EditableTableCell.displayName = "EditableTableCell";
export default EditableTableCell;
