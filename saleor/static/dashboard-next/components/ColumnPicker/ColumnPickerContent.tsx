import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { Theme } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import makeStyles from "@material-ui/styles/makeStyles";
import classNames from "classnames";
import React from "react";

import useElementScroll from "@saleor/hooks/useElementScroll";
import i18n from "@saleor/i18n";
import { isSelected } from "@saleor/utils/lists";
import ControlledCheckbox from "../ControlledCheckbox";
import Hr from "../Hr";

export interface ColumnPickerChoice {
  label: string;
  value: string;
}
export interface ColumnPickerContentProps {
  columns: ColumnPickerChoice[];
  selectedColumns: string[];
}

const useStyles = makeStyles((theme: Theme) => ({
  actionBar: {
    display: "flex",
    justifyContent: "space-between"
  },
  actionBarContainer: {
    boxShadow: `0px 0px 0px 0px ${theme.palette.background.paper}`,
    transition: theme.transitions.duration.short + "ms"
  },
  content: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 3,
    gridTemplateColumns: "repeat(3, 1fr)",
    maxHeight: 256,
    overflowX: "visible",
    overflowY: "scroll",
    padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 3}px`
  },
  contentContainer: {
    padding: 0
  },
  dropShadow: {
    boxShadow: `0px -5px 10px 0px ${theme.overrides.MuiCard.root.borderColor}`
  }
}));

const ColumnPickerContent: React.FC<ColumnPickerContentProps> = props => {
  const { columns, selectedColumns } = props;
  const classes = useStyles(props);
  const anchor = React.useRef<HTMLDivElement>();
  const scrollPosition = useElementScroll(anchor);

  const dropShadow = anchor.current
    ? scrollPosition.y + anchor.current.clientHeight <
      anchor.current.scrollHeight
    : false;

  return (
    <Card>
      <CardContent>
        <Typography color="textSecondary">
          {i18n.t(
            "{{ numberOfSelected }} columns selected out of {{ numberOfTotal }}",
            {
              context: "pick columns to display",
              numberOfSelected: selectedColumns.length,
              numberOfTotal: columns.length
            }
          )}
        </Typography>
      </CardContent>
      <Hr />
      <CardContent className={classes.contentContainer}>
        <div className={classes.content} ref={anchor}>
          {columns.map(column => (
            <ControlledCheckbox
              checked={isSelected(
                column.value,
                selectedColumns,
                (a, b) => a === b
              )}
              name={column.value}
              label={column.label}
              onChange={() => undefined}
            />
          ))}
        </div>
      </CardContent>
      <Hr />
      <CardContent
        className={classNames(classes.actionBarContainer, {
          [classes.dropShadow]: dropShadow
        })}
      >
        <div className={classes.actionBar}>
          <Button color="default">{i18n.t("Reset")}</Button>
          <div>
            <Button color="default">{i18n.t("Cancel")}</Button>
            <Button color="primary" variant="contained">
              {i18n.t("Save")}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ColumnPickerContent;
