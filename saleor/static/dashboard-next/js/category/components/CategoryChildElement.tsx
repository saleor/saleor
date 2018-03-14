import * as React from "react";
import ButtonBase from "material-ui/ButtonBase";
import Card, { CardHeader } from "material-ui/Card";
import Paper from "material-ui/Paper";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import Folder from "material-ui-icons/Folder";

import Skeleton from "../../components/Skeleton";

interface CategoryChildElementProps {
  label: string;
  url: string;
  loading?: boolean;
}

const decorate = withStyles(theme => ({
  button: {
    backgroundColor: theme.palette.background.paper,
    boxShadow: theme.shadows[2],
    color: theme.palette.getContrastText(theme.palette.background.paper),
    justifyContent: "flex-start" as "flex-start",
    transition: theme.transitions.create(["background-color", "box-shadow"], {
      duration: theme.transitions.duration.short
    }),
    width: "100%",
    "&$keyboardFocused": {
      boxShadow: theme.shadows[6]
    },
    "&:active": {
      boxShadow: theme.shadows[8]
    },
    "&$disabled": {
      boxShadow: theme.shadows[0],
      backgroundColor: theme.palette.action.disabledBackground
    },
    "&:hover": {
      backgroundColor: theme.palette.grey.A100,
      // Reset on mouse devices
      "@media (hover: none)": {
        backgroundColor: theme.palette.grey[300]
      },
      "&$disabled": {
        backgroundColor: theme.palette.action.disabledBackground
      }
    }
  }
}));

export const CategoryChildElement = decorate<CategoryChildElementProps>(
  ({ classes, label, url, loading }) => (
    <ButtonBase
      focusRipple
      className={classes.button}
      component={props => <Link to={url} {...props} />}
    >
      <CardHeader
        avatar={<Folder />}
        title={loading ? <Skeleton style={{ width: "80%" }} /> : label}
      />
    </ButtonBase>
  )
);

export default CategoryChildElement;
