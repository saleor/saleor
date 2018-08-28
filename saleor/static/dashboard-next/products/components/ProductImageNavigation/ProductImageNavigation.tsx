import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductImageNavigationProps {
  disabled: boolean;
  images?: Array<{
    id: string;
    url: string;
  }>;
  highlighted?: string;
  onRowClick: (id: string) => () => void;
}

const decorate = withStyles(theme => ({
  card: {
    marginBottom: 2 * theme.spacing.unit
  },
  highlightedImageContainer: {
    borderColor: theme.palette.primary.main
  },
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    background: "#ffffff",
    border: "2px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    cursor: "pointer" as "pointer",
    height: 48,
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit / 2,
    position: "relative" as "relative"
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridRowGap: theme.spacing.unit + "px",
    gridTemplateColumns: "repeat(4, 1fr)"
  },
  toolbar: { marginTop: -theme.spacing.unit / 2 }
}));
const ProductImageNavigation = decorate<ProductImageNavigationProps>(
  ({ classes, highlighted, images, onRowClick }) => (
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
