import * as React from "react";
import ButtonBase from "material-ui/ButtonBase";
import Grid from "material-ui/Grid";
import Card, { CardContent, CardMedia } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import { withStyles } from "material-ui/styles";
import { grey } from "material-ui/colors";
import Skeleton from "../../components/Skeleton";

interface CategoryChildElementProps {
  label: string;
  url: string;
  price: string;
  thumbnail: string;
  loading?: boolean;
}

const decorate = withStyles(theme => ({
  button: {
    backgroundColor: theme.palette.background.paper,
    boxShadow: theme.shadows[2],
    color: theme.palette.getContrastText(theme.palette.background.paper),
    display: "block",
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
  },
  media: {
    backgroundSize: "contain",
    height: 200
  },
  content: {
    height: "5rem"
  },
  price: {
    color: grey[500]
  }
}));

export const ProductChildElement = decorate<CategoryChildElementProps>(
  ({ label, price, url, thumbnail, classes, loading }) => (
    <ButtonBase
      focusRipple
      className={classes.button}
      component={props => <Link to={url} {...props} />}
    >
      <CardMedia image={thumbnail} className={classes.media} />
      <CardContent className={classes.content}>
        {loading ? (
          <Typography variant="button">
            <Skeleton style={{ width: "80%" }} />
          </Typography>
        ) : (
          <>
            <Typography variant="button">{label}</Typography>
            <Typography className={classes.price}>{price}</Typography>
          </>
        )}
      </CardContent>
    </ButtonBase>
  )
);

export default ProductChildElement;
