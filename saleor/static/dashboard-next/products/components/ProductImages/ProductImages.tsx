import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import GridListTile from "@material-ui/core/GridListTile";
import GridListTileBar from "@material-ui/core/GridListTileBar";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import ModeEditIcon from "@material-ui/icons/ModeEdit";
import * as React from "react";
import { SortableContainer, SortableElement } from "react-sortable-hoc";

import PageHeader from "../../../components/PageHeader";
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
  onImageEdit?(id: string);
  onImageUpload?(event: React.ChangeEvent<any>);
  onImageReorder?(event: { oldIndex: number; newIndex: number });
}

interface ImageListElementProps {
  tile: {
    id: string;
    alt?: string;
    sortOrder: number;
    url: string;
  };
  onImageEdit(event: React.ChangeEvent<any>);
}

interface ImageListContainerProps {
  items: any;
  onImageEdit(id: string);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridRowGap: `${theme.spacing.unit * 2}px`,
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
    cursor: "move",
    userSelect: "none" as "none",
    "& img": {
      height: 20 * theme.spacing.unit,
      pointerEvents: "none" as "none",
      width: 20 * theme.spacing.unit
    }
  },
  icon: {
    color: "rgba(255, 255, 255, 0.54)"
  },
  fileField: {
    display: "none"
  }
}));

const ImageListElement = SortableElement(
  decorate<ImageListElementProps>(({ classes, onImageEdit, tile }) => (
    <GridListTile key={tile.id} component="div" className={classes.gridElement}>
      <img src={tile.url} alt={tile.alt} />
      <GridListTileBar
        title={tile.alt || i18n.t("No description")}
        actionIcon={
          onImageEdit ? (
            <IconButton className={classes.icon} onClick={onImageEdit}>
              <ModeEditIcon />
            </IconButton>
          ) : (
            ""
          )
        }
      />
    </GridListTile>
  ))
);

const ImageListContainer = SortableContainer(
  decorate<ImageListContainerProps>(
    ({ classes, items, onImageEdit, ...props }) => {
      return (
        <div {...props}>
          {items.map((image, index) => (
            <ImageListElement
              key={`item-${index}`}
              index={index}
              tile={image}
              onImageEdit={onImageEdit ? onImageEdit(image.id) : null}
            />
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
    onImageReorder,
    onImageUpload
  }) => (
    <Card className={classes.card}>
      <PageHeader title={i18n.t("Images")}>
        <IconButton onClick={e => this.upload.click()} disabled={loading}>
          <AddIcon />
        </IconButton>
        <input
          className={classes.fileField}
          id="fileUpload"
          onChange={onImageUpload}
          type="file"
          ref={ref => (this.upload = ref)}
        />
      </PageHeader>
      <CardContent>
        {images === undefined || images === null ? (
          <div className={classes.root}>
            <GridListTile className={classes.gridElement} component="div">
              <img src={placeholderImage} />
              <GridListTileBar title={i18n.t("Loading...")} />
            </GridListTile>
          </div>
        ) : images.length > 0 ? (
          <ImageListContainer
            axis="xy"
            items={images}
            onSortEnd={onImageReorder}
            className={classes.root}
            onImageEdit={onImageEdit}
          />
        ) : (
          <Typography>{i18n.t("No images available")}</Typography>
        )}
      </CardContent>
    </Card>
  )
);
export default ProductImages;
