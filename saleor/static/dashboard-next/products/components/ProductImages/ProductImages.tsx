import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import DialogContentText from "@material-ui/core/DialogContentText";

import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import * as React from "react";
import { SortableContainer } from "react-sortable-hoc";
import ActionDialog from "../../../components/ActionDialog";
import CardTitle from "../../../components/CardTitle";
import Image from "../../../components/Image";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";

interface ProductImagesProps {
  placeholderImage?: string;
  images?: Array<{
    id: string;
    alt?: string;
    sortOrder: number;
    url: string;
  }>;
  loading?: boolean;
  onImageDelete: (id: string) => () => void;
  onImageEdit: (id: string) => () => void;
  onImageUpload?(event: React.ChangeEvent<any>);
  onImageReorder?(event: { oldIndex: number; newIndex: number });
}

interface ImageListContainerProps {
  items: any;
  onImageDelete: (id: string) => () => void;
  onImageEdit: (id: string) => () => void;
}

const decorate = withStyles(theme => ({
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
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    "&:hover, &.dragged": {
      "& $imageOverlay": {
        display: "block" as "block"
      }
    },
    background: "#ffffff",
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    height: 140,
    margin: "auto",
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit * 2,
    position: "relative" as "relative",
    width: 140
  },
  imageOverlay: {
    background: "rgba(0, 0, 0, 0.6)",
    cursor: "move",
    display: "none" as "none",
    height: 140,
    left: 0,
    padding: theme.spacing.unit * 2,
    position: "absolute" as "absolute",
    top: 0,
    width: 140
  },
  imageOverlayToolbar: {
    alignContent: "flex-end",
    display: "flex" as "flex",
    position: "relative" as "relative",
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
    textAlign: "center" as "center"
  },
  noPhotosIconText: {
    fontSize: "1rem",
    fontWeight: 600 as 600,
    marginTop: theme.spacing.unit
  },
  root: {
    display: "grid" as "grid",
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
}));

const ImageListContainer = SortableContainer(
  decorate<ImageListContainerProps>(
    ({ classes, items, onImageDelete, onImageEdit, ...props }) => {
      return (
        <div {...props}>
          {items.map((image, index) => (
            <Toggle key={index}>
              {(opened, { toggle }) => (
                <>
                  <Image
                    key={`item-${index}`}
                    index={index}
                    tile={image}
                    onImageEdit={onImageEdit ? onImageEdit(image.id) : null}
                    onImageDelete={toggle}
                  />
                  <ActionDialog
                    open={opened}
                    onClose={toggle}
                    onConfirm={() => {
                      onImageDelete(image.id)();
                      toggle();
                    }}
                    variant="delete"
                    title={i18n.t("Remove product image")}
                  >
                    <DialogContentText>
                      {i18n.t("Are you sure you want to delete this image?")}
                    </DialogContentText>
                  </ActionDialog>
                </>
              )}
            </Toggle>
          ))}
        </div>
      );
    }
  )
);

const ProductImages = decorate<ProductImagesProps>(
  ({
    classes,
    images,
    placeholderImage,
    loading,
    onImageEdit,
    onImageDelete,
    onImageReorder,
    onImageUpload
  }) => (
    <Card className={classes.card}>
      <CardTitle
        title={i18n.t("Images")}
        toolbar={
          <>
            <Button
              onClick={() => this.upload.click()}
              disabled={loading}
              variant="flat"
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
export default ProductImages;
