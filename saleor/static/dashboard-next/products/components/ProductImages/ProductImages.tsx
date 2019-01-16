import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";

import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import * as React from "react";
import { SortableContainer, SortableElement } from "react-sortable-hoc";
import CardTitle from "../../../components/CardTitle";
import ImageTile from "../../../components/ImageTile";
import i18n from "../../../i18n";
import { ProductDetails_product_images } from "../../types/ProductDetails";

const styles = (theme: Theme) =>
  createStyles({
    card: {
      marginTop: theme.spacing.unit * 2,
      [theme.breakpoints.down("sm")]: {
        marginTop: 0
      }
    },
    fileField: {
      display: "none"
    },
    icon: {
      color: "rgba(255, 255, 255, 0.54)"
    },
    image: {
      height: "100%",
      objectFit: "contain",
      userSelect: "none",
      width: "100%"
    },
    imageContainer: {
      "&:hover, &.dragged": {
        "& $imageOverlay": {
          display: "block"
        }
      },
      background: "#ffffff",
      border: "1px solid #eaeaea",
      borderRadius: theme.spacing.unit,
      height: 140,
      margin: "auto",
      overflow: "hidden",
      padding: theme.spacing.unit * 2,
      position: "relative",
      width: 140
    },
    imageOverlay: {
      background: "rgba(0, 0, 0, 0.6)",
      cursor: "move",
      display: "none",
      height: 140,
      left: 0,
      padding: theme.spacing.unit * 2,
      position: "absolute",
      top: 0,
      width: 140
    },
    imageOverlayToolbar: {
      alignContent: "flex-end",
      display: "flex",
      position: "relative",
      right: -theme.spacing.unit * 3,
      top: -theme.spacing.unit * 2
    },
    noPhotosIcon: {
      height: theme.spacing.unit * 8,
      margin: "0 auto",
      width: theme.spacing.unit * 8
    },
    noPhotosIconContainer: {
      margin: `${theme.spacing.unit * 5}px 0`,
      textAlign: "center"
    },
    noPhotosIconText: {
      fontSize: "1rem",
      fontWeight: 600,
      marginTop: theme.spacing.unit
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridRowGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "repeat(4, 1fr)",
      [theme.breakpoints.down("sm")]: {
        gridTemplateColumns: "repeat(3, 1fr)"
      },
      [theme.breakpoints.down("xs")]: {
        gridTemplateColumns: "repeat(2, 1fr)"
      }
    }
  });

interface ProductImagesProps extends WithStyles<typeof styles> {
  placeholderImage?: string;
  images: ProductDetails_product_images[];
  loading?: boolean;
  onImageDelete: (id: string) => () => void;
  onImageEdit: (id: string) => () => void;
  onImageUpload?(event: React.ChangeEvent<any>);
  onImageReorder?(event: { oldIndex: number; newIndex: number });
}

interface ImageListContainerProps extends WithStyles<typeof styles> {
  items: any;
  onImageDelete: (id: string) => () => void;
  onImageEdit: (id: string) => () => void;
}

const SortableImage = SortableElement(
  ({ image, onImageEdit, onImageDelete }) => (
    <ImageTile
      image={image}
      onImageEdit={onImageEdit ? () => onImageEdit(image.id) : undefined}
      onImageDelete={onImageDelete}
    />
  )
);

const ImageListContainer = SortableContainer(
  withStyles(styles, { name: "ImageListContainer" })(
    ({
      classes,
      items,
      onImageDelete,
      onImageEdit,
      ...props
    }: ImageListContainerProps) => {
      return (
        <div {...props}>
          {items.map((image, index) => (
            <SortableImage
              key={`item-${index}`}
              index={index}
              image={image}
              onImageEdit={onImageEdit ? onImageEdit(image.id) : null}
              onImageDelete={onImageDelete(image.id)}
            />
          ))}
        </div>
      );
    }
  )
);

const ProductImages = withStyles(styles, { name: "ProductImages" })(
  ({
    classes,
    images,
    placeholderImage,
    loading,
    onImageEdit,
    onImageDelete,
    onImageReorder,
    onImageUpload
  }: ProductImagesProps) => (
    <Card className={classes.card}>
      <CardTitle
        title={i18n.t("Images")}
        toolbar={
          <>
            <Button
              onClick={() => this.upload.click()}
              disabled={loading}
              variant="text"
              color="secondary"
            >
              {i18n.t("Upload image")}
            </Button>
            <input
              className={classes.fileField}
              id="fileUpload"
              onChange={onImageUpload}
              type="file"
              ref={ref => (this.upload = ref)}
            />
          </>
        }
      />
      <CardContent>
        {images === undefined ? (
          <div className={classes.root}>
            <div className={classes.imageContainer}>
              <img className={classes.image} src={placeholderImage} />
            </div>
          </div>
        ) : images.length > 0 ? (
          <ImageListContainer
            distance={20}
            helperClass="dragged"
            axis="xy"
            items={images}
            onSortEnd={onImageReorder}
            className={classes.root}
            onImageDelete={onImageDelete}
            onImageEdit={onImageEdit}
          />
        ) : (
          <div className={classes.noPhotosIconContainer}>
            <AddPhotoIcon className={classes.noPhotosIcon} />
            <Typography className={classes.noPhotosIconText}>
              {i18n.t("Drop images to upload")}
            </Typography>
          </div>
        )}
      </CardContent>
    </Card>
  )
);
ProductImages.displayName = "ProductImages";
export default ProductImages;
