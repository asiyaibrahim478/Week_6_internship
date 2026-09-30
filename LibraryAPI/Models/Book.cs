namespace LibraryAPI.Models
{
    public class Book
    {
        public int Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Author { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public int? PublishedYear { get; set; }
        public string? ISBN { get; set; }
        public bool IsAvailable { get; set; } = true;

        // Optional Relational Foreign Key navigation
        public int? AuthorId { get; set; }
        public Author? AuthorEntity { get; set; }

        public ICollection<Category> Categories { get; set; } = new List<Category>();
    }
}
