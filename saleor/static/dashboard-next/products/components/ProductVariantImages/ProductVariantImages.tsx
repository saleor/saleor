import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import GridListTile from "@material-ui/core/GridListTile";
import GridListTileBar from "@material-ui/core/GridListTileBar";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface ProductVariantImagesProps {
  images?: Array<{
    id: string;
    alt: string;
    url: string;
    order: number;
  }>;
  placeholderImage?: string;
  loading?: boolean;
  onImageAdd();
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridRowGap: `${theme.spacing.unit * 2}px`,
    [theme.breakpoints.down("md")]: {
      gridTemplateColumns: "repeat(3, 1fr)"
    },
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "repeat(2, 1fr)"
    }
  },
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
  }
}));

export const ProductVariantImages = decorate<ProductVariantImagesProps>(
  ({ classes, images, placeholderImage, loading, onImageAdd }) => (
    <Card className={classes.card}>
      <PageHeader title={i18n.t("Images")}>
        <IconButton
          onClick={loading ? () => {} : onImageAdd}
          disabled={loading}
        >
          <AddIcon />
        </IconButton>
      </PageHeader>
      <CardContent>
        <div className={classes.root}>
          {images === undefined || images === null ? (
            <GridListTile className={classes.gridElement} component="div">
              <img src={placeholderImage} />
              <GridListTileBar title={i18n.t("Loading...")} />
            </GridListTile>
          ) : images.length > 0 ? (
            images
              .sort((prev, next) => (prev.order > next.order ? 1 : -1))
              .map(tile => (
                <GridListTile
                  key={tile.id}
                  className={classes.gridElement}
                  component="div"
                >
                  <img src={tile.url} alt={tile.alt} />
                  <GridListTileBar
                    title={tile.alt || i18n.t("No description")}
                  />
                </GridListTile>
              ))
          ) : (
            <Typography>{i18n.t("No images available")}</Typography>
          )}
        </div>
      </CardContent>
    </Card>
  )
);
export default ProductVariantImages;
