import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import * as React from "react";
import { SortableContainer, SortableElement } from "react-sortable-hoc";

import CardTitle from "../../../components/CardTitle";
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
    cursor: "move",
    height: "100%",
    maxHeight: theme.spacing.unit * 15,
    maxWidth: theme.spacing.unit * 15,
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    padding: theme.spacing.unit * 2
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
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridRowGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "repeat(4, 1fr)",
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "repeat(2, 1fr)"
    }
  }
}));

const ImageListElement = SortableElement(
  decorate<ImageListElementProps>(({ classes, onImageEdit, tile }) => (
    <div className={classes.imageContainer}>
      <img className={classes.image} src={tile.url} alt={tile.alt} />
    </div>
    // <GridListTile key={tile.id} component="div" className={classes.gridElement}>
    //   <img src={tile.url} alt={tile.alt} />
    //   <GridListTileBar
    //     title={tile.alt || i18n.t("No description")}
    //     actionIcon={
    //       onImageEdit ? (
    //         <IconButton className={classes.icon} onClick={onImageEdit}>
    //           <ModeEditIcon />
    //         </IconButton>
    //       ) : (
    //         ""
    //       )
    //     }
    //   />
    // </GridListTile>
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
      <CardTitle
        title={i18n.t("Images")}
        toolbar={
          <>
            <Button
              onClick={e => this.upload.click()}
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
              <img src={placeholderImage} />
            </div>
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
