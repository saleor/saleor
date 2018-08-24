import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import { ProductImageType } from "../..";
import i18n from "../../../i18n";

const decorate = withStyles(theme => ({
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    background: "#ffffff",
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    cursor: "pointer" as "pointer",
    height: theme.spacing.unit * 21.5,
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit * 2,
    position: "relative" as "relative",
    transitionDuration: theme.transitions.duration.standard + "ms"
  },
  root: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridRowGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "repeat(3, 1fr)",
    maxWidth: "100%",
    width: theme.breakpoints.values.lg,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "repeat(2, 1fr)"
    }
  },
  selectedImageContainer: {
    borderColor: theme.palette.primary.main
  }
}));

interface ProductVariantImageSelectDialogProps {
  images?: ProductImageType[];
  selectedImages?: string[];
  open: boolean;
  onClose();
  onImageSelect(id: string);
}

const ProductVariantImageSelectDialog = decorate<
  ProductVariantImageSelectDialogProps
>(({ classes, images, open, selectedImages, onClose, onImageSelect }) => (
  <Dialog open={open}>
    <DialogTitle>{i18n.t("Image selection", { context: "title" })}</DialogTitle>
    <DialogContent>
      <div className={classes.root}>
        {images
          .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
          .map(tile => (
            <div
              className={classNames([
                classes.imageContainer,
                {
                  [classes.selectedImageContainer]:
                    selectedImages.indexOf(tile.id) === -1
                }
              ])}
              onClick={onImageSelect(tile.id)}
              key={tile.id}
            >
              <img className={classes.image} src={tile.url} />
            </div>
          ))}
      </div>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>
        {i18n.t("Close", { context: "button" })}
      </Button>
    </DialogActions>
  </Dialog>
));
export default ProductVariantImageSelectDialog;
