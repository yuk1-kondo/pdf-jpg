using NeonPdfShot.DotNet.Models;
using Windows.Data.Pdf;
using Windows.Foundation;
using Windows.Graphics.Imaging;
using Windows.Storage;
using Windows.Storage.Streams;

namespace NeonPdfShot.DotNet.Services;

public sealed class PdfConversionService
{
    public async Task ConvertAsync(
        IReadOnlyList<string> pdfFiles,
        string outputDirectory,
        int dpi,
        int jpegQuality,
        IProgress<ConversionProgress> progress,
        CancellationToken cancellationToken)
    {
        if (pdfFiles.Count == 0)
        {
            throw new InvalidOperationException("PDF files are not selected.");
        }

        var totalPages = await CountPagesAsync(pdfFiles, cancellationToken);
        if (totalPages == 0)
        {
            throw new InvalidOperationException("No pages found in selected PDF files.");
        }

        var outputFolder = await StorageFolder.GetFolderFromPathAsync(outputDirectory);
        var donePages = 0;

        foreach (var pdfPath in pdfFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var baseName = Path.GetFileNameWithoutExtension(pdfPath);
            var sourceFile = await StorageFile.GetFileFromPathAsync(pdfPath);
            await using var sourceStream = await sourceFile.OpenReadAsync();
            var document = await PdfDocument.LoadFromStreamAsync(sourceStream);

            for (uint i = 0; i < document.PageCount; i++)
            {
                cancellationToken.ThrowIfCancellationRequested();

                using var page = document.GetPage(i);
                await RenderPageAsJpegAsync(page, outputFolder, baseName, i + 1, dpi, jpegQuality);

                donePages++;
                var percent = (int)Math.Round(donePages * 100.0 / totalPages, MidpointRounding.AwayFromZero);
                progress.Report(new ConversionProgress(percent, $"Converted {baseName} page {i + 1}"));
            }
        }
    }

    private static async Task<int> CountPagesAsync(IReadOnlyList<string> pdfFiles, CancellationToken cancellationToken)
    {
        var totalPages = 0;
        foreach (var pdfPath in pdfFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var sourceFile = await StorageFile.GetFileFromPathAsync(pdfPath);
            await using var sourceStream = await sourceFile.OpenReadAsync();
            var document = await PdfDocument.LoadFromStreamAsync(sourceStream);
            totalPages += (int)document.PageCount;
        }

        return totalPages;
    }

    private static async Task RenderPageAsJpegAsync(
        PdfPage page,
        StorageFolder outputFolder,
        string baseName,
        uint pageNumber,
        int dpi,
        int jpegQuality)
    {
        var width = (uint)Math.Max(1, Math.Round(page.Size.Width * dpi / 72.0));
        var height = (uint)Math.Max(1, Math.Round(page.Size.Height * dpi / 72.0));

        await using var renderedStream = new InMemoryRandomAccessStream();
        await page.RenderToStreamAsync(renderedStream, new PdfPageRenderOptions
        {
            DestinationWidth = width,
            DestinationHeight = height,
        });

        renderedStream.Seek(0);
        var decoder = await BitmapDecoder.CreateAsync(renderedStream);
        var pixelData = await decoder.GetPixelDataAsync(
            BitmapPixelFormat.Bgra8,
            BitmapAlphaMode.Ignore,
            new BitmapTransform(),
            ExifOrientationMode.IgnoreExifOrientation,
            ColorManagementMode.ColorManageToSRgb);

        var outputName = $"{baseName}_page_{pageNumber:000}.jpg";
        var outputFile = await outputFolder.CreateFileAsync(outputName, CreationCollisionOption.ReplaceExisting);
        await using var outputStream = await outputFile.OpenAsync(FileAccessMode.ReadWrite);

        var qualityProps = new BitmapPropertySet
        {
            {
                "ImageQuality",
                new BitmapTypedValue((double)jpegQuality / 100.0, PropertyType.Single)
            },
        };

        var encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.JpegEncoderId, outputStream, qualityProps);
        encoder.SetPixelData(
            BitmapPixelFormat.Bgra8,
            BitmapAlphaMode.Ignore,
            decoder.PixelWidth,
            decoder.PixelHeight,
            decoder.DpiX,
            decoder.DpiY,
            pixelData.DetachPixelData());

        await encoder.FlushAsync();
    }
}
