import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";

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
    margin: "auto",
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
    padding: theme.spacing.unit * 2,
    position: "absolute" as "absolute",
    top: 0,
    width: 148
  },
  imageOverlayToolbar: {
    alignContent: "flex-end",
    display: "flex" as "flex",
    position: "relative" as "relative",
    right: -theme.spacing.unit * 4,
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
  deleteIcon: boolean;
  editIcon: boolean;
  onImageDelete?: () => void;
  onImageEdit?: (event: React.ChangeEvent<any>) => void;
  index?: string;
}

const Image = decorate<ImageProps>(
  ({ classes, onImageDelete, onImageEdit, tile, editIcon, deleteIcon }) => (
    <div className={classes.imageContainer}>
      <div className={classes.imageOverlay}>
        <div className={classes.imageOverlayToolbar}>
          {editIcon ? (
            <IconButton color="secondary" onClick={onImageEdit}>
              <EditIcon />
            </IconButton>
          ) : null}
          {deleteIcon ? (
            <IconButton color="secondary" onClick={onImageDelete}>
              <DeleteIcon />
            </IconButton>
          ) : null}
        </div>
      </div>
      <img className={classes.image} src={tile.url} alt={tile.alt} />
    </div>
  )
);

export default Image;
