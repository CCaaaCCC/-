export type FileValidationRule = {
  allowedExtensions: string[];
  maxSizeMB: number;
  extensionMessage: string;
  sizeMessage: string;
};

const normalizeExtension = (filename: string) => {
  return (filename.split('.').pop() || '').toLowerCase();
};

export const createFileValidator = (
  rule: FileValidationRule,
  onError: (message: string) => void,
) => {
  return (file: File) => {
    const ext = normalizeExtension(file.name);
    if (!rule.allowedExtensions.includes(ext)) {
      onError(rule.extensionMessage);
      return false;
    }

    if (file.size > rule.maxSizeMB * 1024 * 1024) {
      onError(rule.sizeMessage);
      return false;
    }

    return true;
  };
};
