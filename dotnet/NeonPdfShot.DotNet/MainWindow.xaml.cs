using System.Collections.ObjectModel;
using System.IO;
using System.Windows;
using System.Windows.Media;
using Microsoft.Win32;
using NeonPdfShot.DotNet.Models;
using NeonPdfShot.DotNet.Services;
using Forms = System.Windows.Forms;

namespace NeonPdfShot.DotNet;

public partial class MainWindow : Window
{
    private readonly ObservableCollection<string> _pdfFiles = [];
    private readonly PdfConversionService _conversionService = new();

    public MainWindow()
    {
        InitializeComponent();
        PdfList.ItemsSource = _pdfFiles;

        OutputFolderText.Text =
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
        ConvertButton.IsEnabled = false;
    }

    private void SelectFiles_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "PDF files (*.pdf)|*.pdf",
            Multiselect = true,
            CheckFileExists = true,
            Title = "Select PDF files",
        };

        if (dialog.ShowDialog() == true)
        {
            AddFiles(dialog.FileNames);
        }
    }

    private void ClearFiles_Click(object sender, RoutedEventArgs e)
    {
        _pdfFiles.Clear();
        ConvertButton.IsEnabled = false;
        Log("Cleared selected files.");
    }

    private void ChooseOutput_Click(object sender, RoutedEventArgs e)
    {
        using var dialog = new Forms.FolderBrowserDialog
        {
            Description = "Choose output folder",
            UseDescriptionForTitle = true,
            InitialDirectory = OutputFolderText.Text,
            ShowNewFolderButton = true,
        };

        if (dialog.ShowDialog() == Forms.DialogResult.OK)
        {
            OutputFolderText.Text = dialog.SelectedPath;
            Log($"Output: {dialog.SelectedPath}");
        }
    }

    private async void Convert_Click(object sender, RoutedEventArgs e)
    {
        if (_pdfFiles.Count == 0)
        {
            MessageBox.Show("Please select at least one PDF file.", "No PDF", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!Directory.Exists(OutputFolderText.Text))
        {
            MessageBox.Show("Output folder does not exist.", "Invalid folder", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!int.TryParse(DpiTextBox.Text, out var dpi) || dpi is < 72 or > 600)
        {
            MessageBox.Show("DPI must be a number between 72 and 600.", "Invalid DPI", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var quality = (int)QualitySlider.Value;
        SetBusyState(true);
        ProgressBar.Value = 0;
        Log("--- Conversion started ---");

        var progress = new Progress<ConversionProgress>(p =>
        {
            ProgressBar.Value = p.Percent;
            Log(p.Message);
        });

        try
        {
            await _conversionService.ConvertAsync(_pdfFiles.ToList(), OutputFolderText.Text, dpi, quality, progress, CancellationToken.None);
            Log("--- Conversion completed ---");
            MessageBox.Show("PDF to JPG conversion completed.", "Done", MessageBoxButton.OK, MessageBoxImage.Information);
        }
        catch (Exception ex)
        {
            Log($"Error: {ex.Message}");
            MessageBox.Show(ex.Message, "Conversion failed", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            SetBusyState(false);
        }
    }

    private void DropZone_DragOver(object sender, System.Windows.DragEventArgs e)
    {
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            e.Effects = DragDropEffects.Copy;
            DropZone.BorderBrush = new SolidColorBrush(Color.FromRgb(90, 253, 224));
            DropZone.Background = new SolidColorBrush(Color.FromArgb(90, 7, 85, 110));
        }
        else
        {
            e.Effects = DragDropEffects.None;
        }
    }

    private void DropZone_DragLeave(object sender, System.Windows.DragEventArgs e)
    {
        DropZone.BorderBrush = new SolidColorBrush(Color.FromRgb(98, 168, 255));
        DropZone.Background = new SolidColorBrush(Color.FromArgb(34, 22, 60, 103));
    }

    private void DropZone_Drop(object sender, System.Windows.DragEventArgs e)
    {
        DropZone_DragLeave(sender, e);

        if (!e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            return;
        }

        var files = (string[])e.Data.GetData(DataFormats.FileDrop);
        AddFiles(files);
    }

    private void QualitySlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (QualityValueText is not null)
        {
            QualityValueText.Text = ((int)QualitySlider.Value).ToString();
        }
    }

    private void AddFiles(IEnumerable<string> candidates)
    {
        var added = 0;
        foreach (var file in candidates)
        {
            if (!File.Exists(file))
            {
                continue;
            }

            if (!string.Equals(Path.GetExtension(file), ".pdf", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (_pdfFiles.Contains(file))
            {
                continue;
            }

            _pdfFiles.Add(file);
            added++;
        }

        ConvertButton.IsEnabled = _pdfFiles.Count > 0;
        Log($"Loaded {added} PDF file(s). Total: {_pdfFiles.Count}");
    }

    private void SetBusyState(bool isBusy)
    {
        ConvertButton.IsEnabled = !isBusy && _pdfFiles.Count > 0;
        DpiTextBox.IsEnabled = !isBusy;
        QualitySlider.IsEnabled = !isBusy;
        OutputFolderText.IsEnabled = !isBusy;
    }

    private void Log(string text)
    {
        LogText.AppendText($"{DateTime.Now:HH:mm:ss}  {text}{Environment.NewLine}");
        LogText.ScrollToEnd();
    }
}
