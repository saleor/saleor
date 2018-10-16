import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import { ProductDetails_product_images_edges_node } from "../../products/types/ProductDetails";

const decorate = withStyles(theme => ({
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
    height: 148,
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit * 2,
    position: "relative" as "relative",
    width: 148
  },
  imageOverlay: {
    background: "rgba(0, 0, 0, 0.6)",
    cursor: "move",
    display: "none" as "none",
    height: 148,
    left: 0,
    position: "absolute" as "absolute",
    top: 0,
    width: 148
  },
  imageOverlayToolbar: {
    display: "flex" as "flex",
    justifyContent: "flex-end"
  }
}));

interface ImageTileProps {
  image: ProductDetails_product_images_edges_node;
  deleteIcon: boolean;
  editIcon: boolean;
  onImageDelete?: () => void;
  onImageEdit: (event: React.ChangeEvent<any>) => void;
}

const ImageTile = decorate<ImageTileProps>(
  ({ classes, onImageDelete, onImageEdit, image, editIcon, deleteIcon }) => (
    <div className={classes.imageContainer}>
      <div className={classes.imageOverlay}>
        <div className={classes.imageOverlayToolbar}>
          {editIcon && (
            <IconButton color="secondary" onClick={onImageEdit}>
              <EditIcon />
            </IconButton>
          )}
          {deleteIcon && (
            <IconButton color="secondary" onClick={onImageDelete}>
              <DeleteIcon />
            </IconButton>
          )}
        </div>
      </div>
      <img className={classes.image} src={image.url} alt={image.alt} />
    </div>
  )
);

export default ImageTile;
