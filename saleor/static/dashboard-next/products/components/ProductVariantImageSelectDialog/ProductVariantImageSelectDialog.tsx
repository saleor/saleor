import CheckCircleIcon from "@material-ui/icons/CheckCircle";
import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle
} from "material-ui/Dialog";
import GridList, { GridListTile, GridListTileBar } from "material-ui/GridList";
import IconButton from "material-ui/IconButton";
import Subheader from "material-ui/List/ListSubheader";
import { withStyles, WithStyles } from "material-ui/styles";
import * as React from "react";

import i18n from "../../../i18n";

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridRowGap: `${theme.spacing.unit * 2}px`,
    width: theme.breakpoints.values.lg,
    maxWidth: "100%",
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "repeat(2, 1fr)"
    }
  },
  gridElement: {
    "& img": {
      width: "100%"
    }
  },
  icon: {
    color: "white"
  },
  iconChecked: {
    color: theme.palette.secondary.main
  }
}));

interface ProductVariantImageSelectDialogProps {
  images?: Array<{
    id: string;
    url: string;
    alt: string;
    order: number;
  }>;
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
      WithStyles<"root" | "gridElement" | "icon" | "iconChecked">,
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

    handleConfirm = () => this.state.images;
    handleImageSelect = id => () =>
      this.state.images.indexOf(id) === -1
        ? this.setState(prevState => ({ images: [...prevState.images, id] }))
        : this.setState(prevState => ({
            images: prevState.images.filter(image => image !== id)
          }));

    render() {
      const {
        children,
        classes,
        images,
        open,
        onConfirm,
        onClose
      } = this.props;
      return (
        <Dialog open={open}>
          <DialogTitle>
            {i18n.t("Image selection", { context: "title" })}
          </DialogTitle>
          <DialogContent>
            <DialogContentText>{i18n.t("Select images")}</DialogContentText>
            <div className={classes.root}>
              {images
                .sort((prev, next) => (prev.order > next.order ? 1 : -1))
                .map(tile => (
                  <GridListTile
                    key={tile.id}
                    className={classes.gridElement}
                    component="div"
                    onClick={this.handleImageSelect(tile.id)}
                  >
                    <img src={tile.url} alt={tile.alt} />
                    <GridListTileBar
                      title={tile.alt || i18n.t("No description")}
                      actionIcon={
                        <IconButton
                          className={
                            this.state.images.indexOf(tile.id) !== -1
                              ? classes.iconChecked
                              : classes.icon
                          }
                        >
                          <CheckCircleIcon />
                        </IconButton>
                      }
                    />
                  </GridListTile>
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
