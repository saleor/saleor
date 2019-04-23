import * as React from "react";

import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { CollectionCreateInput } from "../../types/globalTypes";
import CollectionCreatePage from "../components/CollectionCreatePage/CollectionCreatePage";
import { TypedCollectionCreateMutation } from "../mutations";
import { CreateCollection } from "../types/CreateCollection";
import { collectionListUrl, collectionUrl } from "../urls";

export const CollectionCreate: React.StatelessComponent<{}> = () => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handleCollectionCreateSuccess = (data: CreateCollection) => {
    if (data.collectionCreate.errors.length === 0) {
      notify({
        text: i18n.t("Created collection", {
          context: "notification"
        })
      });
      navigate(collectionUrl(data.collectionCreate.collection.id));
    } else {
      const backgroundImageError = data.collectionCreate.errors.find(
        error =>
          error.field === ("backgroundImage" as keyof CollectionCreateInput)
      );
      if (backgroundImageError) {
        notify({
          text: backgroundImageError.message
        });
      }
    }
  };
  return (
    <TypedCollectionCreateMutation onCompleted={handleCollectionCreateSuccess}>
      {(createCollection, { called, data, loading }) => {
        const formTransitionState = getMutationState(
          called,
          loading,
          maybe(() => data.collectionCreate.errors)
        );
        return (
          <>
            <WindowTitle title={i18n.t("Create collection")} />
            <CollectionCreatePage
              errors={maybe(() => data.collectionCreate.errors, [])}
              onBack={() => navigate(collectionListUrl())}
              disabled={loading}
              onSubmit={formData =>
                createCollection({
                  variables: {
                    input: {
                      backgroundImage: formData.backgroundImage.value,
                      backgroundImageAlt: formData.backgroundImageAlt,
                      descriptionJson: JSON.stringify(formData.description),
                      isPublished: formData.isPublished,
                      name: formData.name,
                      seo: {
                        description: formData.seoDescription,
                        title: formData.seoTitle
                      }
                    }
                  }
                })
              }
              saveButtonBarState={formTransitionState}
            />
          </>
        );
      }}
    </TypedCollectionCreateMutation>
  );
};
export default CollectionCreate;
