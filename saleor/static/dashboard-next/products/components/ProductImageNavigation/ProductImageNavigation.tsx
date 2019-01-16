import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    card: {
      marginBottom: 2 * theme.spacing.unit
    },
    highlightedImageContainer: {
      borderColor: theme.palette.primary.main
    },
    image: {
      height: "100%",
      objectFit: "contain",
      userSelect: "none",
      width: "100%"
    },
    imageContainer: {
      background: "#ffffff",
      border: "2px solid #eaeaea",
      borderRadius: theme.spacing.unit,
      cursor: "pointer",
      height: 48,
      overflow: "hidden",
      padding: theme.spacing.unit / 2,
      position: "relative"
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridRowGap: theme.spacing.unit + "px",
      gridTemplateColumns: "repeat(4, 1fr)"
    },
    toolbar: { marginTop: -theme.spacing.unit / 2 }
  });

interface ProductImageNavigationProps extends WithStyles<typeof styles> {
  disabled: boolean;
  images?: Array<{
    id: string;
    url: string;
  }>;
  highlighted?: string;
  onRowClick: (id: string) => () => void;
}

const ProductImageNavigation = withStyles(styles, {
  name: "ProductImageNavigation"
})(
  ({
    classes,
    highlighted,
    images,
    onRowClick
  }: ProductImageNavigationProps) => (
    <Card className={classes.card}>
      <CardTitle title={i18n.t("All photos")} />
      <CardContent>
        {images === undefined ? (
          <Skeleton />
        ) : (
          <div className={classes.root}>
            {images.map(image => (
              <div
                className={classNames({
                  [classes.imageContainer]: true,
                  [classes.highlightedImageContainer]: image.id === highlighted
                })}
                onClick={onRowClick(image.id)}
                key={image.id}
              >
                <img className={classes.image} src={image.url} />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
);
ProductImageNavigation.displayName = "ProductImageNavigation";
export default ProductImageNavigation;
