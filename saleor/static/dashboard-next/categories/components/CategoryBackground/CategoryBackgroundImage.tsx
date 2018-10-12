import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Image from "../../../components/Image";
import Toggle from "../../../components/Toggle";
import CategoryDelete from "../CategoryDelete";

const decorate = withStyles({});

interface BackgroundImageProps {
  onImageDelete?: (id: string) => () => void;
  backgroundImage?: {
    url?: string;
  };
}

const BackgroundImage = decorate<BackgroundImageProps>(
  ({ onImageDelete, backgroundImage }) => (
    <Toggle>
      {(opened, { toggle }) => (
        <>
          <Image tile={backgroundImage} onImageDelete={toggle} />
          <CategoryDelete
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

export default BackgroundImage;
