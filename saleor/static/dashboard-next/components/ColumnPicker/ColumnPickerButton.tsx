import Button from "@material-ui/core/Button";
import { Theme } from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import ArrowDropDownIcon from "@material-ui/icons/ArrowDropDown";
import makeStyles from "@material-ui/styles/makeStyles";
import classNames from "classnames";
import React from "react";

import i18n from "@saleor/i18n";

interface ColumnPickerButtonProps {
  active: boolean;
  className?: string;
  onClick: () => void;
}

const useStyles = makeStyles(
  (theme: Theme) => ({
    icon: {
      marginLeft: theme.spacing.unit * 2,
      transition: theme.transitions.duration.short + "ms"
    },
    root: {
      "& span": {
        color: theme.palette.primary.main
      },
      paddingRight: theme.spacing.unit
    },
    rootActive: {
      background: fade(theme.palette.primary.main, 0.1)
    },
    rotate: {
      transform: "rotate(180deg)"
    }
  }),
  {
    name: "ColumnPickerButton"
  }
);

const ColumnPickerButton: React.FC<ColumnPickerButtonProps> = props => {
  const { active, className, onClick } = props;
  const classes = useStyles(props);

  return (
    <Button
      className={classNames(classes.root, className, {
        [classes.rootActive]: active
      })}
      color="primary"
      onClick={onClick}
      variant="outlined"
    >
      {i18n.t("Columns", {
        context: "select visible columns button"
      })}
      <ArrowDropDownIcon
        color="primary"
        className={classNames(classes.icon, {
          [classes.rotate]: active
        })}
      />
    </Button>
  );
};

export default ColumnPickerButton;
