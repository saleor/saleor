import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import { SortableElement } from "react-sortable-hoc";

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
  }
}));

interface ImageProps {
  tile?: {
    id?: string;
    alt?: string;
    sortOrder?: number;
    url?: string;
  };
  onImageDelete?: () => void;
  onImageEdit?: (event: React.ChangeEvent<any>) => void;
  index?: string;
}

const Image = SortableElement(
  decorate<ImageProps>(({ classes, onImageDelete, onImageEdit, tile }) => (
    <div className={classes.imageContainer}>
      <div className={classes.imageOverlay}>
        <div className={classes.imageOverlayToolbar}>
          {onImageEdit !== undefined ? (
            <IconButton color="secondary" onClick={onImageEdit}>
              <EditIcon />
            </IconButton>
          ) : null}
          {onImageDelete !== undefined ? (
            <IconButton color="secondary" onClick={onImageDelete}>
              <DeleteIcon />
            </IconButton>
          ) : null}
        </div>
      </div>
      <img className={classes.image} src={tile.url} alt={tile.alt} />
    </div>
  ))
);

export default Image;
