import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import ImageTile from "../../../components/ImageTile";
import Toggle from "../../../components/Toggle";
import CategoryDeleteImage from "../CategoryDeleteImage";

const decorate = withStyles({});

interface CategoryBackgroundImageProps {
  onImageDelete?: (id: string) => () => void;
  backgroundImage?: {
    url?: string;
  };
}

const CategoryBackgroundImage = decorate<CategoryBackgroundImageProps>(
  ({ onImageDelete, backgroundImage }) => (
    <Toggle>
      {(opened, { toggle }) => (
        <>
          <ImageTile
            tile={backgroundImage}
            onImageDelete={toggle}
            deleteIcon={true}
            editIcon={false}
          />
          <CategoryDeleteImage
            open={opened}
            onClose={toggle}
            onConfirm={() => {
              onImageDelete(backgroundImage.url)();
              toggle();
            }}
            title={"Remove category background"}
            dialogText={"Are you sure you want to delete this image?"}
          />
        </>
      )}
    </Toggle>
  )
);

export default CategoryBackgroundImage;
