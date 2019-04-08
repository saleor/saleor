import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";

const styles = (theme: Theme) =>
  createStyles({
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
      background: theme.palette.background.paper,
      border: `1px solid ${theme.overrides.MuiCard.root.borderColor}`,
      borderRadius: theme.spacing.unit,
      height: 148,
      overflow: "hidden",
      padding: theme.spacing.unit * 2,
      position: "relative",
      width: 148
    },
    imageOverlay: {
      background: "rgba(0, 0, 0, 0.6)",
      cursor: "move",
      display: "none",
      height: 148,
      left: 0,
      position: "absolute",
      top: 0,
      width: 148
    },
    imageOverlayToolbar: {
      display: "flex",
      justifyContent: "flex-end"
    }
  });

interface ImageTileProps extends WithStyles<typeof styles> {
  image: {
    alt?: string;
    url: string;
  };
  onImageDelete?: () => void;
  onImageEdit?: (event: React.ChangeEvent<any>) => void;
}

const ImageTile = withStyles(styles, { name: "ImageTile" })(
  ({ classes, onImageDelete, onImageEdit, image }: ImageTileProps) => (
    <div className={classes.imageContainer}>
      <div className={classes.imageOverlay}>
        <div className={classes.imageOverlayToolbar}>
          {onImageEdit && (
            <IconButton color="primary" onClick={onImageEdit}>
              <EditIcon />
            </IconButton>
          )}
          {onImageDelete && (
            <IconButton color="primary" onClick={onImageDelete}>
              <DeleteIcon />
            </IconButton>
          )}
        </div>
      </div>
      <img className={classes.image} src={image.url} alt={image.alt} />
    </div>
  )
);
ImageTile.displayName = "ImageTile";
export default ImageTile;
