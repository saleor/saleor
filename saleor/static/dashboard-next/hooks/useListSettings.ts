import useLocalStorage from "@saleor/hooks/useLocalStorage";
import { defaultListSettings } from "./../config";
import { ListSettings, ListViews } from "./../types";

export default function useListSettings(listName: ListViews) {
  const [settings, setListSettings] = useLocalStorage(
    "listConfig",
    defaultListSettings
  );
  const updateListSettings = (key: keyof ListSettings, value: any) => {
    setListSettings(settings => ({
      ...settings,
      [listName]: {
        ...settings[listName],
        [key]: value
      }
    }));
  };

  return {
    settings: settings[listName],
    updateListSettings
  };
}
