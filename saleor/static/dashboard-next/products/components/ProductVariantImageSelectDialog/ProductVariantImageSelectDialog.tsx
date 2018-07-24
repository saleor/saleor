import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import GridListTile from "@material-ui/core/GridListTile";
import GridListTileBar from "@material-ui/core/GridListTileBar";
import IconButton from "@material-ui/core/IconButton";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import CheckCircleIcon from "@material-ui/icons/CheckCircle";
import * as React from "react";

import { ProductImageType } from "../..";
import i18n from "../../../i18n";

const decorate = withStyles(theme => ({
  gridElement: {
    "& img": {
      width: "100%"
    }
  },
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    "&.selected": {
      borderColor: theme.palette.primary.main
    },
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
  }
}));

interface ProductVariantImageSelectDialogProps {
  images?: ProductImageType[];
  selectedImages?: Array<{
    id: string;
  }>;
  open: boolean;
  onClose?();
  onConfirm?(images: string[]);
}

interface ProductVariantImageSelectDialogState {
  images: string[];
}

const ProductVariantImageSelectDialog = decorate<
  ProductVariantImageSelectDialogProps
>(
  class ProductVariantImageSelectDialogComponent extends React.Component<
    ProductVariantImageSelectDialogProps &
      WithStyles<"root" | "gridElement" | "image" | "imageContainer">,
    ProductVariantImageSelectDialogState
  > {
    constructor(props) {
      super(props);
      this.state = {
        images: this.props.selectedImages
          ? this.props.selectedImages.map(image => image.id)
          : []
      };
    }

    handleConfirm = () => this.props.onConfirm(this.state.images);
    handleImageSelect = id => () =>
      this.state.images.indexOf(id) === -1
        ? this.setState(prevState => ({ images: [...prevState.images, id] }))
        : this.setState(prevState => ({
            images: prevState.images.filter(image => image !== id)
          }));

    render() {
      const { classes, images, open, onClose } = this.props;
      return (
        <Dialog open={open}>
          <DialogTitle>
            {i18n.t("Image selection", { context: "title" })}
          </DialogTitle>
          <DialogContent>
            <div className={classes.root}>
              {images
                .sort(
                  (prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1)
                )
                .map(tile => (
                  <div
                    className={[
                      classes.imageContainer,
                      this.state.images.indexOf(tile.id) === -1
                        ? undefined
                        : "selected"
                    ].join(" ")}
                    onClick={this.handleImageSelect(tile.id)}
                  >
                    <img
                      className={classes.image}
                      src={tile.url}
                      alt={tile.alt}
                    />
                  </div>
                ))}
            </div>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>
              {i18n.t("Cancel", { context: "button" })}
            </Button>
            <Button
              variant="raised"
              onClick={this.handleConfirm}
              color="primary"
            >
              {i18n.t("Save", { context: "button" })}
            </Button>
          </DialogActions>
        </Dialog>
      );
    }
  }
);

export default ProductVariantImageSelectDialog;
