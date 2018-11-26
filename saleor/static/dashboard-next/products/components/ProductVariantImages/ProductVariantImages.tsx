import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { ProductImage } from "../../types/ProductImage";

interface ProductVariantImagesProps {
  images?: ProductImage[];
  placeholderImage?: string;
  disabled: boolean;
  onImageAdd();
}

const decorate = withStyles(theme => ({
  card: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: 0
    }
  },
  gridElement: {
    "& img": {
      width: "100%"
    }
  },
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    width: "100%"
  },
  imageContainer: {
    background: "#ffffff",
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    height: theme.spacing.unit * 17.5,
    marginBottom: theme.spacing.unit * 2,
    padding: theme.spacing.unit * 2
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "repeat(4, 1fr)"
  }
}));

export const ProductVariantImages = decorate<ProductVariantImagesProps>(
  ({ classes, disabled, images, onImageAdd }) => (
    <Card className={classes.card}>
      <CardTitle
        title={i18n.t("Images")}
        toolbar={
          <Button
            color="secondary"
            variant="flat"
            disabled={disabled}
            onClick={onImageAdd}
          >
            {i18n.t("Choose photos")}
          </Button>
        }
      />
      <CardContent>
        <div className={classes.root}>
          {images === undefined || images === null ? (
            <Skeleton />
          ) : images.length > 0 ? (
            images
              .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
              .map(tile => (
                <div className={classes.imageContainer} key={tile.id}>
                  <img className={classes.image} src={tile.url} />
                </div>
              ))
          ) : (
            <Typography>{i18n.t("No images available")}</Typography>
          )}
        </div>
      </CardContent>
    </Card>
  )
);
ProductVariantImages.displayName = "ProductVariantImages";
export default ProductVariantImages;
